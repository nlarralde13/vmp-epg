#Convert uplynk channel schedule to EPG
import  urllib, zlib, hmac, hashlib, time, json, datetime, base64, csv
import configparser
from pprint import pprint
import boto3
import requests
import configparser
import xml.etree.ElementTree as xml
 

config = configparser.ConfigParser()
config.read("credentials.conf")
channel_id = config.get('credentials', 'channel_id') # Channel ID you wish to Use
auth_header = True # True: New api/v4 pass the msg / sig through the header | False: Do it the old way

owner = config.get('credentials', 'userid') # uplynk owner id
api_key = config.get('credentials', 'apikey') # uplynk api key
xml_file = 'epg.xml'

ROOT_URL = 'https://services.uplynk.com'
ROOT_URLv4 = 'https://services-auswuat1.uplynk.com/api/v4'
OWNER = config.get('credentials', 'userid')
SECRET = config.get('credentials', 'apikey')
CHID = config.get('credentials', 'channel_id')
BUCKET = config.get('credentials', 's3_bucket')

# This helps create ISO 8601 Timestamps needed for the API
def convert_ts(utc_tstamp):
    """ Convert a utc timestamp to ISO 8601 formatted standard of YYYY-MM-DDThh:mm:ss.sZ
        :param utc_tstamp: The UTC timestamp to convert (expected milliseconds)
        # TODO: Perhaps support more than timestamps in milliseconds - but for now 99% of our timestamps
        # are in milliseconds

        :return: ISO 8601 formatted standard of YYYY-MM-DDThh:mm:ss.sZ
    """
    iso_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    try:
        _ts = float("{0:.3f}".format(utc_tstamp/1000.0))
        return "{}{}".format(datetime.datetime.utcfromtimestamp(_ts).strftime(iso_format)[:-4], "Z")
    except Exception:
        print ("BAD TIMESTAMP - CAN'T CONVERT: {}".format(utc_tstamp))
        raise


#Basic Uplynk Call to API
def Call(uri, **msg):
    msg['_owner'] = OWNER
    msg['_timestamp'] = int(time.time())
    msg = json.dumps(msg)
    msg = zlib.compress(msg, 9).encode('base64').strip()
    sig = hmac.new(str(SECRET), msg, hashlib.sha256).hexdigest()
    body = urllib.urlencode(dict(msg=msg, sig=sig))
    return json.loads(urllib2.urlopen(ROOT_URL + uri, body).read())

#API v4 Channel Call to UAT ZOne
def call_api(api_service, method='get', **kwargs):
    #print ("\n<<<<<<<<<<<< NEW {} REQUEST >>>>>>>>>>>>\n".format(method.upper()))
    headers, params = None, None
    method = method.lower()

    url = '{}{}'.format(ROOT_URLv4, api_service)
    msg = {}
    msg['_owner'] = owner
    msg['_timestamp'] = int(time.time())
    msg = json.dumps(msg).encode()
    msg = base64.b64encode(zlib.compress(msg, 9)).strip()
    sig = hmac.new(api_key.encode(), msg, hashlib.sha256).hexdigest().encode()

    headers = {
            'Content-Type': 'application/json',
        }

    if auth_header:
        headers['Authorization'] = msg + b' ' + sig
        #print ("Using Header For Auth: {}".format(headers))
        params = {'headers': headers}
    else:
        #print ("Using Params For Auth: {}".format({'msg':msg, 'sig':sig}))
        params = {'params': {'msg':msg, 'sig':sig}, 'headers':headers}

    if method == 'get':
        response = requests.get(url, **params)
    elif method == 'patch':
        response = requests.patch(url, data=json.dumps(dict(**kwargs)), **params)
    elif method == 'post':
        response = requests.post(url, data=json.dumps(dict(**kwargs)), **params)
    elif method == 'delete':
        response = requests.delete(url, **params)

    #print ("Called URL: {}".format(response.url))
    #print ("\nRESPONSE SERVER ID: {}".format(response.headers.get('X-Services')))
    #pp ("RESPONSE HEADERS: {}".format(response.headers))
    #print ("\nResponse JSON:")

    if int(response.status_code) < 500:
        x = response.json()
        return x
    else:
        print ("\nREALLY BAD API ERROR:")
        ppprint(response.content)


#Write to S3
#Client Access Tools for BOTO3
client = boto3.client(
    's3', 
    aws_secret_access_key = config.get('credentials', 'aws_secret_access_key'),
    aws_access_key_id = config.get('credentials', 'aws_access_key_id'),
    region_name = 'us-east-1'

)
#Resource Access TOols for BOTO3
resource = boto3.resource(
    's3', 
    aws_secret_access_key = config.get('credentials', 'aws_secret_access_key'),
    aws_access_key_id = config.get('credentials', 'aws_access_key_id'),
    region_name = 'us-east-1'

)
#Grab Channel Schedule using v4 APIs
def get_schedule():
    start = int(time.time() * 1000.0) # NOW
    end = start + (2000 * 60 * 1000)  # x minutes later

    start = convert_ts(start)
    end = convert_ts(end)

    endpoint = '/channels/{}/schedules?start={}&end={}&slicer_assets=1'.format(channel_id, start, end)
    #Begin XML Write
    root = xml.Element('VerizonMediaEPG')

    x = call_api(endpoint, method='get')
    for i in x['items']:
        if i['content_type'] == 'asset' or 'slicer':
            ci = i['content_id']
            title = i['desc']
            start = i['start']
            duration = i['dur']
            content_type = i['content_type']            
            #Channel SubElement
            channel = xml.SubElement(root, "Channel")
            #Add channel details as channel metadata and then pull from api to fill in element details
            xml.SubElement(channel, 'Channel', stationId='NULL', channelNumber='NULL', callSign="NULL", network='NULL', broacastType="digital", gmtOffset='-8', observeDls='true')

            #Show SubElement
            show = xml.SubElement(root, 'Show')
            
            xml.SubElement(show, 'Show', startTime=start, duration=str(duration), stereo="N", cc="N", sap="N", madeForTv="N", letterbox="N", repeat="Y", howCurrent="Replay", hdtv="N", year="", website="")
            xml.SubElement(show, 'Title').text = title
            xml.SubElement(show, 'VMP_Asset_ID').text = ci
            xml.SubElement(show, 'contentType').text = content_type
            xml.SubElement(show, 'DisplayGenre').text = 'News'
            xml.SubElement(show, 'Rating').text = 'Rating'
        
            
    tree=xml.ElementTree(root)
    tree.write(xml_file, encoding='UTF-8', xml_declaration=True)
            
   
   
get_schedule()


#Get Bucket names
def getBuckets():
    clientResponse = client.list_buckets()
    for bucket in clientResponse['Buckets']:
        pprint("Bucket Name:" + bucket['Name'])

#Upload to specific S3 Bucket    
s3_upload = client.upload_file(
    Filename = xml_file, #File to Upload
    Bucket = 'vmp-epg', #Bucket name
    Key = xml_file, #What to name the file in S3,
    ExtraArgs = {'ContentType': 'text/xml', 'ACL':'public-read'}
)












