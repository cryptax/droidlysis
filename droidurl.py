#!/usr/bin/env python3

"""
__author__ = "Axelle Apvrille"
__status__ = "Mature"
__license__ = "MIT License"
"""

def build_special_url_list():
    """Returns a list of special URLs"""
    list = []
    
    # dummy URLs
    list.append('^(http://)127\.0\.0\.1$')
    list.append('^8\.8\.8\.8$')
    list.append('^8\.8\.4\.4$')
    list.append('^https*://%s:%d%s')
    list.append('^(http://)*192\.168\.[0-9.:]*')
    list.append('host:port')
    list.append('^(http://)*localhost$') 
    list.append('^https*://$')
    list.append('^https*$')
    list.append('temporary$') 
    list.append('^https*://unknown$') 
    list.append('^https*://images$')
    list.append('^http://ads$')
    list.append('^http://app$')
    list.append('^http://server$')
    list.append('^http://server/.*')
    list.append('username:password@YOUR')
    list.append('www\.dummyurl\.com')


    # clean URLs - which do not correspond to a kit i.e with a smali path
    list.append('creativecommons\.org')
    list.append('docs\.google\.')
    list.append('jsoup\.org')
    list.append('www\.jcip\.net')
    list.append('finance\.google\.')
    list.append('maps\.google') 
    list.append('^https*://play\.google\.com')
    list.append('https*://[a-zA-Z]*\.google\.com/') 
    list.append('www\.google\.') 
    list.append('checkout\.google\.com')
    list.append('\.google-analytics\.com') 
    list.append('^https*://[a-z]*\.googleapis\.com/')
    list.append('plus\.url\.google\.com') 
    list.append('market\.android\.com')
    list.append('source\.android\.com')
    list.append('material\.io')
    list.append('java\.sun\.com') 
    list.append('\.facebook\.com/help') 
    list.append('\.facebook\.com$') 
    list.append('forum\.xda-developers\.com/showthread\.php')
    list.append('mozilla\.org') 
    list.append('www\.android\.com') 
    list.append('developer\.android\.com/reference/')
    list.append('fontforge\.sf\.net')
    list.append('www\.apache\.org')  
    list.append('www\.apple\.com')
    list.append('travis-ci\.org')
    list.append('twitter\.com') 
    list.append('www\.gnu\.org')
    list.append('www\.fsf\.org')
    list.append('www\.iec\.ch')
    list.append('www\.paypal\.com')
    list.append('www\.macromedia\.com/go/getflashplayer')
    list.append('www\.mozilla\.org') 
    list.append('opensource\.org') 
    list.append('www\.openssl\.org') 
    list.append('www\.gstatic\.com') 
    list.append('www\.JSON\.org') 
    list.append('www\.junit\.com') 
    list.append('http://www\.amazon\.com/gp/mas/dl/android') 
    list.append('.\.youtube.com') 
    list.append('\.hockeyapp\.net') 
    list.append('http://ns\.adobe\.com/') 
    list.append('https*://[a-zA-Z]*\.jquery\.com')
    list.append('https*://jqueryui\.com')
    list.append('^https*://jquery\.[com|org]/*$')
    list.append('scripts\.sil\.org')
    list.append('www\.ajaxplorer\.info')
    list.append('wikipedia\.org')
    list.append('play\.google\.com')
    list.append('github\.com')
    list.append('jquery\.org')
    list.append('www\.iana\.org')


        # AV
    list.append('www\.fortinet\.com') 
    list.append('docs\.fortinet\.com/fclient/android/')
    list.append('home\.mcafee\.com')
    list.append('\.norton\.com') 
    list.append('www\.avast\.com')
    list.append('\.symantec\.com') 
    list.append('www\.mcafeemobilesecurity\.com/eula\.aspx') 
    list.append('www\.trendmicro\.com') 
    list.append('https*://[a-zA-Z0-9]*\.360safe\.com')

        # search engines
    list.append('search\.twitter\.com') 
    list.append('search\.yahoo\.com') 
    list.append('www\.baidu\.com') 
    list.append('wap\.baidu\.com') 
    list.append('map\.baidu\.com') 
    list.append('www\.searchmobileonline\.com') 


        # XML
    list.append('^https*://push$') 
    list.append('^https*://schemas') 
    list.append('^https*://www\.$') 
    list.append('www\.w3\.org') 
    list.append('xml\.apache\.org') 
    list.append('xml\.org') 
    list.append('xmlpull\.org') 
    list.append('^https*://.*/configure[-_0-9]*\.dtd$')
    
        # Operator
    list.append('10\.0\.0\.172') 
    list.append('10\.0\.0\.200') 
    list.append('wap\.uni-info\.com\.cn') 
    list.append('mmsc\.myuni\.com\.cn') 
    list.append('mmsc\.vnet\.mobi') 
    list.append('wap\.vnet\.mobi') 
    list.append('10\.151\.0\.1') 
    list.append('62\.201\.134\.17') 
    list.append('mmsbouygtel\.com') 
    list.append('\.monternet\.com') 

    # Protocol
    list.append('oauth_token') 

    # adkit urls which sometimes appear outside the smali path
    list.append('pflexads\.com')
    list.append('admob\.com')
    list.append('^https*://api\.weibo\.com')
    list.append('^https*://.*\.alipay.com')

    return list

        
