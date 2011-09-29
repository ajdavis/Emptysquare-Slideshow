#!/usr/bin/env python
"""
Requires Python 2.7 or better

notes 2010-09-17 emptysquare.net flickrapi

key 24b43252c30181f08bd549edbb3ed394
secret 2f58307171bc644e
"""

from __future__ import print_function
import webbrowser
import re
import os
import sys
import simplejson
import flickrapi # from http://pypi.python.org/pypi/flickrapi
import argparse # Python 2.7 module
import zipfile

from tornado.web import template

api_key = '24b43252c30181f08bd549edbb3ed394'

parser = argparse.ArgumentParser(description='Update emptysquare slideshow from your Flickr account')
parser.add_argument(dest='flickr_username', action='store', help='Your Flickr username')
parser.add_argument(dest='set_name', action='store', help='The (case-sensitive) name of the Flickr set to use')
parser.add_argument('--article-title', default=None, help='The title of the related article (for back-to-article link)')
parser.add_argument('--back-to-article-link', default=None, help='URL of the related article (for back-to-article link')
parser.add_argument('--show-titles', type=bool, default=False, help='Whether to show individual photos\' titles')
parser.add_argument('--no-browser', type=bool, default=False, help="Don't open a web browser to display the slideshow")

## {{{ http://code.activestate.com/recipes/577257/ (r2)
_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".
    """
    import unicodedata
    if not isinstance(value, unicode):
        value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)
## end of http://code.activestate.com/recipes/577257/ }}}


def parse_flickr_json(json_string):
    """
    @param json_string: Like jsonFlickrApi({'key':'value', ...})
    @return: A native Python object, like dictionary or list
    """
    prefix = 'jsonFlickrApi('
    if json_string.startswith(prefix):
        json_string = json_string[len(prefix):]
        
        # Also ends with ')'
        json_string = json_string[:-1]
    
    return simplejson.loads(json_string)

def dump_json(obj):
    """
    @param obj: A native Python object, like dictionary or list
    @return: A string, the object dumped as pretty, parsable JSON
    """
    return simplejson.dumps(obj, sort_keys=True, indent=' ')

class JSONFlickr(object):
    def __init__(self, api_key):
        """
        @param api_key: A Flickr API key
        """
        self.flickr = flickrapi.FlickrAPI(api_key)
    
    def __getattr__(self, attr):
        def f(**kwargs):
            kwargs_copy = kwargs.copy()
            kwargs_copy['format'] = 'json'
            return parse_flickr_json(
                getattr(self.flickr, attr)(**kwargs_copy)
            )

        return f

def get_photoset(flickr_username, set_name):
    json_flickr = JSONFlickr(api_key)
    
    print('Getting user id')
    user_id = json_flickr.people_findByUsername(
        username=flickr_username
    )['user']['nsid']
    
    print(user_id)
    
    print('Getting set')
    sets = json_flickr.photosets_getList(user_id=user_id)['photosets']['photoset']
    
    try:
        # TODO: recurse, find set even if isn't top-level
        emptysquare_set = [
            _set for _set in sets
            if _set['title']['_content'] == set_name
        ][0]
    except IndexError:
        raise Exception("Couldn't find Flickr set named %s" % repr(set_name))
    
    print('Extracting photoset %s' % repr(set_name))
    photos = json_flickr.photosets_getPhotos(photoset_id=emptysquare_set['id'])['photoset']
    photos['title'] = set_name # Add title to returned data

    # Add image URLs and descriptions to the photo info returned by photosets_getPhotos()
    for photo in photos['photo']:
        photo['flickr_url'] = 'http://www.flickr.com/photos/%s/%s' % (
            flickr_username, photo['id']
        )
        
        sizes = json_flickr.photos_getSizes(photo_id=photo['id'])['sizes']['size']
        
        try:
            medium_640_size = [
                size for size in sizes
                if size['label'] == 'Medium 640'
            ][0]
            
            # Store the source URL in photo, so it'll get saved to the photo set's
            # cache file
            photo['source'] = medium_640_size['source']
        except IndexError:
            raise Exception(
                "Couldn't find 'Medium 640' size for photo %s at %s" % (
                    repr(photo['title']),
                    repr(photo['flickr_url'])
                )
            )
        
        info = json_flickr.photos_getInfo(photo_id=photo['id'])['photo']
        photo['description'] = info['description']['_content'].replace('\n', '<br/>')
        photo['owner_realname'] = info['owner']['realname']
        
        sys.stdout.write('.'); sys.stdout.flush()
    
    sys.stdout.write('\n')
    
    return photos

def make_zip(html_filename, directory_name, zipfilename):
    print('Making zip file')
    with zipfile.ZipFile(zipfilename, 'w') as zf:
        for fname in [
            html_filename,
            'cc.png',
            'emptysquare_slideshow.css',
            'emptysquare_slideshow.js',
            'emptysquare_slideshow_arrow_left.gif',
            'emptysquare_slideshow_arrow_right.gif',
            'emptysquare_slideshow_cc_icon.gif',
            'emptysquare_slideshow_flickr_icon.gif',
            'emptysquare_slideshow_lodown_logo.gif',
        ]:
            zf.write(
                filename=fname,
                arcname=os.path.join(directory_name, fname),
            )

def make_html(source, destination, photos, args):
    source_contents = open(source).read()
    with file(destination, 'w+') as f:
        f.write(
            template.Template(
                source_contents,
                autoescape=None,
            ).generate(**{
                'title': photos['title'],
                'total_photos': photos['total'],
                'photos_info_json': dump_json(photos),
                'article_title': args.article_title,
                'back_to_article_link': args.back_to_article_link,
                'show_titles': 'true' if args.show_titles else 'false',
            })
        )

if __name__ == '__main__':
    args = parser.parse_args()
    source = 'emptysquare_slideshow_template.html'
    destination = 'index.html'
    photos = get_photoset(args.flickr_username, args.set_name)
    make_html(source, destination, photos, args)
    print(destination)
    zipfilename = slugify(args.set_name) + '.zip'
    make_zip(destination, slugify(args.set_name), zipfilename)
    print(zipfilename)
    if not args.no_browser:
        print('Opening web browser...')
        webbrowser.open('file://' + os.path.abspath(destination))
