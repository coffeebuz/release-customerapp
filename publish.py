#!/usr/bin/python

"""Uploads an apk to the test track."""

import argparse
import sys
import os
from apiclient import sample_tools
from oauth2client import client
from apiclient.discovery import build
import httplib2
import mimetypes
import yaml

release = yaml.safe_load(open('Release.yml'))
releaseNotes = '\n'.join(release['notes'])
APK_VERSION_SHA = release['apk_sha_version']
TRACK = 'internal'  # Can be 'alpha', beta', 'production' or 'rollout'
mimetypes.add_type('application/vnd.android.package-archive', '.apk')
# Declare command-line flags.
argparser = argparse.ArgumentParser(add_help=False)
argparser.add_argument('package_name',
                       help='The package name. Example: com.android.sample')
argparser.add_argument('apk_file',
                       nargs='?',
                       default=('{}.apk'.format(APK_VERSION_SHA)),
                       help='The path to the APK file to upload.')

SERVICE_ACCOUNT_EMAIL = ( os.environ['GPLAY_SERVICE_ACCOUNT_EMAIL'] )

def main(argv):
  # Authenticate and construct service.
  # Load the key in PKCS 12 format that you downloaded from the Google APIs
  # Console when you created your Service account.
  f = open('publishingapikey.p12', 'rb')
  key = f.read()
  f.close()

  # Create an httplib2.Http object to handle our HTTP requests and authorize it
  # with the Credentials. Note that the first parameter, service_account_name,
  # is the Email address created for the Service account. It must be the email
  # address associated with the key that was created.
  credentials = client.SignedJwtAssertionCredentials(
      SERVICE_ACCOUNT_EMAIL,
      key,
      scope='https://www.googleapis.com/auth/androidpublisher')
  http = httplib2.Http()
  http = credentials.authorize(http)

  service = build('androidpublisher', 'v3', http=http)
  
  # Process flags and read their values.
  flags = argparser.parse_args()

  package_name = flags.package_name
  apk_file = flags.apk_file

  try:
    edit_request = service.edits().insert(body={}, packageName=package_name)
    result = edit_request.execute()
    edit_id = result['id']

    apk_response = service.edits().apks().upload(
        editId=edit_id,
        packageName=package_name,
        media_body=apk_file).execute()

    versionCode = apk_response['versionCode'] 
    print ('Version code {} has been uploaded'.format( versionCode ))

    track_response = service.edits().tracks().update(
        editId=edit_id,
        track=TRACK,
        packageName=package_name,
        body={u'releases': [{
            u'name': release['name'],
            u'releaseNotes': [{
                u'language' : 'en-AU',
                u'text' : releaseNotes
            }],
            u'versionCodes': [versionCode],
            u'status': u'draft',
        }]}).execute()

    print ( 'Track {} is set with releases: {}'.format (
        track_response['track'], str(track_response['releases'])) )

    commit_request = service.edits().commit(
        editId=edit_id, packageName=package_name).execute()

    print ('Edit "{}" has been committed'.format (commit_request['id']))

  except client.AccessTokenRefreshError:
    print ('The credentials have been revoked or expired, please re-run the '
           'application to re-authorize')

if __name__ == '__main__':
  main(sys.argv)