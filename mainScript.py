from nltk.stem.wordnet import WordNetLemmatizer
from BeautifulSoup import BeautifulSoup
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from google import search
import networkx  as nx
import cPickle
import urllib2
import copy
import time
import re



# Function to do a google search on a bandname and save the Wikipedia URL/ Darklyric URL
# To be run rarely since takes huge amout of time
# Run it once and save the URLs into a cPickle 
def getBandInfo():
	# read data, replace once ready to read stuff from internet
	bandWikiInfo = {} ;
	bandLyricLinkInfo = {} ;
	f = open('100Bands.txt','r') ;
	bandinfo= []
	for line in f.readlines():
		t = line.split('.') ;
		line = t[1].strip()
		#print 'Getting Wiki URL for ' + line # uncomment this for getting WikiURL
		print 'Getting Lyrics URL for ' + line # uncomment this for getting Lyrics URL
		
		#query = line + 'band wiki';  # uncomment this for getting WikiURL
		query = line + 'lyrics darklyrics'; # uncomment this for getting Lyrics URL
		i= 0
		for urls in search(query, stop=1):
			if i==0:
				wikiUrl = urls 
				break
			i = i+1 ;	
		#bandWikiInfo[line] =  wikiUrl ;  # uncomment this for getting WikiURL
		bandLyricLinkInfo[line] = wikiUrl # uncomment this for getting Lyrics URL
	#return bandWikiInfo ; # uncomment this for getting WikiURL
	return bandLyricLinkInfo ; # uncomment this for getting Lyrics URL


#parse the Wikipedia URLs to extract Information 
# only extracting genre
# later, if have time, extract other stuff too !
def parseWiki(wikiList):
	bandGenreInfo = {}
	bandAsActInfo = {}
	for key in wikiList:
		#key = 'Slipknot'
		turl = wikiList[key] ;
		print 'Looking up band ' + key
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		page = opener.open(turl)
		soup = BeautifulSoup(page.read())
		tables = soup.findChildren('table')
		if(len(tables)>0):
			table = tables[0] ;  # first table has the genre information
			if(len(tables[0]) < 10):   # some have some other crap, in that case select the next table
				table = tables[1]	
			rows = table.findChildren('tr') 
			# Usually 3rd/4th/5th row has genre information
			# hence loop through to find out
			assact = []
			genre = []
			if(len(rows) >= 5):
				for i in range(1,len(rows)):
					t = rows[i].findChildren('a');
					h =  rows[i].findChildren('th');
					if(len(t) >= 1 and  t[0].string == 'Genres'):
						genre_row  = rows[i] ;
						all_a = genre_row.findChildren('a') 
						all_a = all_a[1:] 
				
						
						for info in all_a:
							if(info.string is not None):
								genre.append(info.string.lower()) ;
					elif(len(h) >=1 and h[0].string == 'Associated acts'):
						origin_row = rows[i];
						all_a = origin_row.findChildren('a') ;
						
						for info in all_a:
							if(info.string is not None):
								assact.append(info.string.lower()) ;
						
				#print genre + '\n'
				if(len(genre)<1):
					genre = ['Unknown']
				if(len(assact)<1):
					assact = ['Unknown']
				
				bandGenreInfo[key]  = genre
				bandAsActInfo[key] = assact
				#print genre, assact
			else :# Unknown Issue
				bandGenreInfo[key] = ['Unknown']
				bandAsActInfo[key] = ['Unknown']
		else:
			bandGenreInfo[key] = ['Unknown']
			bandAsActInfo[key] = ['Unknown']
			
		#break;
	#return rows
	return bandGenreInfo, bandAsActInfo


def getRawLyrics(soup):
	for e in soup.findAll('br'):
		e.extract()
	
	for e in soup.findAll('i'):
		e.extract()
	for e in soup.findAll('h3'):
		e.extract()
	for e in soup.findAll('a'):
		e.extract()
	for e in soup.findAll('div'):
		e.extract()
	result = ''
	for item in soup.contents:
		result = result + item
	return result
	



# hit appropriate lyric website, 
# get appropriate band link
# hit it again and download lyrics
def parseLyrics(lyricList,outlist,s,e):
	baseURL = u'http://www.darklyrics.com' 
	i = 0 ;
	for key in lyricList :
		i = i + 1 ;
		if(i >= s and i<= e):
			#key = 'In Flames'  # REMOVE FOR 100 Bands
			time.sleep(1)
			turl = lyricList[key] ;
			print 'Looking up band ' + key
			#print turl
			opener = urllib2.build_opener()
			opener.addheaders = [('User-agent', 'Mozilla/5.0')]
			page = opener.open(turl)
			soup = BeautifulSoup(page.read())
			divs = soup.findChildren('div',attrs={"class" : "album"})
			#get the sub-URL to the lyrics of the latest album and then full URL to the lyrics source
			if(len(divs)>0):
				sub_url =  divs[len(divs)-1].findChildren('a')[0]['href']
				lurl = baseURL + sub_url.split('#')[0][2:]
				#print lurl
				# hit the URL and get data
				page = opener.open(lurl)
				soup = BeautifulSoup(page.read())
				lydiv = soup.findChildren('div',attrs={"class" : "lyrics"})[0]
				[x.extract() for x in lydiv('div')]
				#lyrictext = re.sub('\'lydiv.text ;
				rly = getRawLyrics(lydiv) 
			else:
				rly = "Manual"
				print rly
			outlist[key] = rly
		#break ; # remove once started full testing
	print 'done' , s, ' to ', e	
	return outlist
	
# Create graph by looking into all possible relations between the nodes

#Given a list of sample lyrics of bands, extract keywords
# match them with master Lyrical keywords to get final lyrical words out
def parseLyrics2(outlist):
	bandLyricInfo = {} 
	master = [['death', 0],['violence',0],['sacrifice',0],['nature',0],['peace',0],['storm',0],['spirit',0],[ 'dark',0],['scream',0],['pain',0],['blood',0],['flesh',0],['love',0],['greed',0],['poison',0],['anger',0],['revenge',0],['misery',0],['hell',0],['heaven',0],['hate',0],['soul',0],['battle',0],['ghost',0],['joy',0],['light',0],['omen',0],['miracle',0],['magic',0],['universe',0],['disease',0],['god',0],['satan',0],['struggle',0],['heart',0]]
	for key in outlist:
		templist = copy.deepcopy(master) ;
		#key = 'Queensryche'
		raw = outlist[key];
		raw = raw.lower();
		words = re.findall(r'\w+', raw,flags = re.UNICODE | re.LOCALE) # punctuation
		imp_words = filter(lambda x: x not in stopwords.words('english'), words) # filter noise
		lmt = WordNetLemmatizer()
		words_new = [lmt.lemmatize(x) for x in words]
		dw = list(set(words_new))
		
		for word in dw:
			for m in templist:
				p1 = wordnet.synsets(word) ;
				p2 = wordnet.synsets(m[0]) ;
				if(len(p1) >0 and len(p2) >0):
					c = p1[0].wup_similarity(p2[0])
					if(c > m[1]):
						m[1] = c
		# sort words according to similarity
		tnew = sorted(templist,key=lambda val:val[1],reverse=True) [0:10] ;
		# remove the other column
		for l in tnew:
			del l[1]
		print 'Done ',key
		#break ;
		bandLyricInfo[key] = tnew
		#del templist
	return bandLyricInfo
	#return templist 





# check for all possible connections between nodes and assign weights
# using a specific weighting function
def CreateGraph(ginfo, linfo, ainfo):
	# initiate graph
	i =0 ;
	g = nx.Graph();
	for name in ginfo:
		g.add_node(name) ;
		g.node[name]['genre'] = ginfo[name]
		g.node[name]['lyrics'] = linfo[name]
		g.node[name]['asact'] = ainfo[name]
	# loop over nodes and add weighted edges whereever possible
	w = [0.45,0.1,0.45]
	for g1 in g.nodes():
		for g2 in g.nodes():
			if(g1 != g2):
				#print g1,g2
				w_genre = len(set(g.node[g1]['genre']).intersection(set(g.node[g2]['genre'])))
				w_lyrics  = len(set(g.node[g1]['lyrics']).intersection(set(g.node[g2]['lyrics'])))
				w_asact  = len(set(g.node[g1]['asact']).intersection(set(g.node[g2]['asact'])))
				W = w[0]*w_genre + w[1]*w_lyrics + w[2]*w_asact ;
				if(W != 0):
					g.add_edge(g1,g2,weight=W) ;
	
	return g 


# Get Recommendations using the above graph
def GetRelatedBands(g,bandname,cutoff):
	
	# use g.neighbors(bandname)
	lst = []
	for v, n, data in g.edges_iter(bandname,True):
		lst.append([n,data['weight']])
	# sort lst based on weight, truncate the top part and then return 
	lst = sorted(lst,key=lambda val:val[1],reverse=True)[0:cutoff] ;
	for l in lst:
		del l[1]
	return lst ;
	


def GetAllResults(g,bandlist):
	finalRec = {}
	for band in bandlist:
		finalRec[band] = GetRelatedBands(g,band,5)
	return finalRec


# GET Wiki/ Lyric URLs
##################################

#listWikiUrls100 = getBandInfo();
#cPickle.dump(listWikiUrls100,open("wikiBandsDetails_100_bands.p","wb"))
#lstLyricUrls100 = getBandInfo(); # comment/uncomment different lines
#cPickle.dump(lstLyricUrls100,open("LyricBandsDetails_100_bands.p","wb"))

#--- USE wikiUR/Lyric URLs to get bandGenreInfo and bandLyricInfo
##############################################


#lst = cPickle.load( open( "wikiBandsDetails_100_bands.p", "rb" ) )
#bandGenreInfo,bandAsActInfo = parseWiki(lst)
#cPickle.dump(bandGenreInfo,open("bandGenreInfo_100.p","wb")) #<---------   CAREFUL
#cPickle.dump(bandAsActInfo,open("bandAsActInfo_100.p","wb")) #<---------   CAREFUL

# !!!!!!!!!!!!!!!!!!!!! WARNING NEVER SAVE outlist again !!!!!!!!!!!!!!!!
#lstl = cPickle.load( open( "LyricBandsDetails_100_bands.p", "rb" ) )
# run the following for all such (m,n) interval from 1 till 100 , MANUALLY
#outlist = parseLyrics(lstl,outlist,1,10)
#cPickle.dump(outlist,open("Lyricoutlist.p","wb"))
#!!!!!!!!!!!!!!!!!!!!!! DON't RUN ABOVE BLOCK !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

#outlist = cPickle.load( open( "Lyricoutlist.p", "rb" ) )
#bandLyricInfo = parseLyrics2(outlist)
#cPickle.dump(bandLyricInfo,open("bandLyricInfo_100.p","wb")) #<--------- CAREFUL


# USE bandGenreInfo and bandLyricInfo to start creating graphs
###########################################

bandGenreInfo = cPickle.load( open( "bandGenreInfo_100.p", "rb" ) )
bandAsActInfo = cPickle.load( open( "bandAsActInfo_100.p", "rb" ) )
bandLyricInfo = cPickle.load( open( "bandLyricInfo_100.p", "rb" ) )


g = CreateGraph(bandGenreInfo,bandLyricInfo,bandAsActInfo) ;

print 'Recommendations if you listen to Slayer: '
print GetRelatedBands(g,'Slayer',5)

print 'Recommendations if you listen to Children of Bodom: '
print GetRelatedBands(g,'Children of Bodom',5)

results = GetAllResults(g,bandGenreInfo)
