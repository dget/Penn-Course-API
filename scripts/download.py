import urllib2, re, codecs, os
from xml.dom.minidom import parseString

# timetable or roster depending on time of year
urlType = "timetable"

# gives us a correct XML version of the URL 
response = urllib2.urlopen("http://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20html%20where%20url%3D%22http%3A%2F%2Fwww.upenn.edu%2Fregistrar%2F" + urlType + "%2F%22%20and%20xpath%3D%22%2F%2Ftd%5B%40class%3D'body'%5D%2Fa%22&diagnostics=false")
html = response.read()

xmldoc = parseString(html)

subjects = [ (link.getAttribute('href'), re.sub('\s+', ' ', link.firstChild.data)) \
             for link in xmldoc.documentElement.firstChild.childNodes if link.getAttribute('href') != '#']

for subject in subjects:
    url = "http://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20html%20where%20url%3D%22http%3A%2F%2Fwww.upenn.edu%2Fregistrar%2F"+ urlType +"%2F" + (subject[0] if subject[0] != "cogs%20.html" else "cogs.html") + "%22%20and%20xpath%3D%22%2F%2Fpre%22"
    print url
    subjdoc = parseString( urllib2.urlopen(url).read())
    outfile = open(subject[0].split('.')[0] + '.txt', 'w')
    outfile.write(subject[1] + '\n')
    outfile.write("".join([codecs.getencoder('ascii')(x.nodeValue, 'ignore')[0] for x in subjdoc.firstChild.firstChild.firstChild.childNodes if x.nodeType==3]))
    outfile.close()

