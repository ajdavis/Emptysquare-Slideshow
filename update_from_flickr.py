#!/usr/bin/env python
"""
Requires Python 2.7 or better

notes 2010-09-17 emptysquare.net flickrapi

key 24b43252c30181f08bd549edbb3ed394
secret 2f58307171bc644e
"""

from __future__ import print_function
import string
import simplejson
import flickrapi # from http://pypi.python.org/pypi/flickrapi
import argparse # Python 2.7 module

api_key = '24b43252c30181f08bd549edbb3ed394'

parser = argparse.ArgumentParser(description='Update emptysquare slideshow from your Flickr account')
parser.add_argument(dest='flickr_username', action='store', help='Your Flickr username')
parser.add_argument(dest='set_name', action='store', help='The (case-sensitive) name of the Flickr set to use')

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
    
    # Add image URLs to the photo info returned by photosets_getPhotos()
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
    
    return photos

def make_html(source, destination, photos):
    source_contents = open(source).read()
    with file(destination, 'w+') as f:
        f.write(
            string.Template(
                source_contents
            ).safe_substitute({ 'photos_info_json': photos })
        )

if __name__ == '__main__':
    args = parser.parse_args()
    source = 'emptysquare_slideshow_template.html'
    destination = 'emptysquare_slideshow.html'
    photos = get_photoset(args.flickr_username, args.set_name)
    make_html(source, destination, photos)
    print('Done')
