import datetime
import xml.etree.ElementTree as xml
 
timeNow = datetime.datetime.now()
AssetName = 'News at 9'

def generate_xml(fileName):
    root = xml.Element('VerizonMediaEPG')
    count = 0
    while True:
        if count > 4:
            break
        else:
            #Channel SubElement
            channel = xml.SubElement(root, "Channel")
            xml.SubElement(channel, 'Channel', stationId='1234567', chanelNumber='123', callSign="KIRO-SB1", network='CBS', broacastType="digital", gmtOffset='-8', observeDls='true')

            #Show SubElement
            show = xml.SubElement(root, 'Show')
            xml.SubElement(show, 'Show', startDate="20210128", startTime="15:00", duration="01:00", eventId="1804072880", stereo="N", cc="N", sap="N", madeForTv="N", letterbox="N", repeat="Y", howCurrent="Replay", hdtv="N", year="", website="", adjustedStartDate="20210128", adjustedStartTime="07:00")
            xml.SubElement(show, 'Title').text = AssetName
            xml.SubElement(show, 'Showtype').text = 'News'
            xml.SubElement(show, 'DisplayGenre').text = 'News'
            xml.SubElement(show, 'Rating').text = 'Rating'


            tree=xml.ElementTree(root)
            tree.write(fileName, encoding='UTF-8', xml_declaration=True)
            count = count + 1

generate_xml('epg_sample.xml')



'''
<TitanTV siteId="53006" value="NowShowing" error="OK">
<Channel stationId="2022891" channelNumber="39" callSign="KIRO-SB1" network="CBS" broadcastType="digital" gmtOffset="-8" observesDls="true">
<Show startDate="20210128" startTime="15:00" duration="01:00" eventId="1804072880" stereo="N" cc="N" sap="N" madeForTv="N" letterbox="N" repeat="Y" howCurrent="Replay" hdtv="N" year="" website="" adjustedStartDate="20210128" adjustedStartTime="07:00">
<Title>KIRO 7 News at 6AM Replay</Title>
<ShowType>News</ShowType>
<DisplayGenre>News</DisplayGenre>
<Rating/>
</Show>
<Show startDate="20210128" startTime="16:00" duration="01:00" eventId="1804072862" stereo="N" cc="N" sap="N" madeForTv="N" letterbox="N" repeat="" howCurrent="" hdtv="N" year="" website="" adjustedStartDate="20210128" adjustedStartTime="08:00">
<Title>KIRO 7 News at 6AM Replay</Title>
<ShowType>News</ShowType>
<DisplayGenre>News</DisplayGenre>
<Rating/>
</Show>
<Show startDate="20210128" startTime="17:00" duration="00:30" eventId="1804072735" stereo="N"
'''