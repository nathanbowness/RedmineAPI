import requests
import logging
from urllib.parse import urljoin


class RedmineInterface(object):
    def __init__(self, url, api_key, wait_between_retry_attempts=60):
        """
        :param url: Redmine url in this format - http://redmine.biodiversity.agr.gc.ca/
        :param api_key: Your redmine api key - You can find your API key on your account page ( /my/account ) 
                 when logged in, on the right-hand pane of the default layout.
        :param wait_between_retry_attempts: How many seconds to wait between retry attempts when accessing Redmine
        """

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel('DEBUG')

        if self.__url_validator(url):
            self.url=url
        else:
            raise RedmineConnectionError("Invalid URL")

        self.wait = wait_between_retry_attempts
        self.api_key = api_key

    def upload_file(self, filepath, issue_id, content_type, file_name_once_uploaded="",
                    additional_notes="", status_change=None):
        """
        :param filepath: Path to the file you want to upload
        :param issue_id: ID of the Redmine issue you want to upload the file to
        :param content_type: The content type of the file you are uploading, please check on this webpage -
                      http://www.freeformatter.com/mime-types-list.html
        :param file_name_once_uploaded: The filename once it's on Redmine
        :param additional_notes: Notes to upload the file with
        :param status_change: Number from 1 - 4, 2 is in progress 4 is feedback
        """

        url = urljoin(self.url, 'uploads.json')
        headers = {'X-Redmine-API-Key': self.api_key, 'content-type': 'application/octet-stream'}
        self.logger.info("Uploading %s to redmine..." % filepath)
        self.logger.info("Sending POST request to %s" % filepath)

        if file_name_once_uploaded == "":
            import os
            file_name_once_uploaded = os.path.split(filepath)[-1]

        resp = requests.post(url, headers=headers, files={file_name_once_uploaded: open(filepath, "rb")})
        import json
        if resp.status_code == 201:
            token = json.loads(resp.content.decode("utf-8"))['upload']['token']
        else:
            err = "Status code %s, Message %s" % (resp.status_code, resp.content.decode("utf-8"))
            self.logger.error("[Error] Problem uploading file to Redmine: " + err)
            raise RedmineUploadError("Failed to upload file to Redmine. Status code %s, Message %s" %
                                     (resp.status_code, resp.content.decode("utf-8")))
        data = {
            "issue": {
                "uploads": [
                    {
                        "token": token,
                        "filename": file_name_once_uploaded,
                        "content_type": content_type
                    }
                ],
                "notes": additional_notes
            }
        }
        if status_change is not None:
            data['issue']['status_id'] = status_change

        self.__put_request_timeout(urljoin(self.url, '/issues/%s.json' % str(issue_id)), data)

    def get_new_issues(self, project='cfia'):
        """
        This will return a dictionary with the newest 25 open issues
        :param project: in the url of your issues page
                 eg. http://redmine.biodiversity.agr.gc.a/projects/cfia/issues
                                                     project is cfia^^^
        """
        self.logger.info("Getting new issues...")
        url = urljoin(self.url, 'projects/%s/issues.json' % project)
        return self.__get_request_timeout(url)

    def get_issue_data(self, issue_id):
        url = urljoin(self.url, 'issues/%s.json' % str(issue_id))
        return self.__get_request_timeout(url)

    def update_issue(self, issue_id, notes=None, status_change=None, assign_to_id=None):
        """
        :param issue_id: Redmine ID of the issue you want to update
        :param notes: What you want to write in the notes
        :param status_change: Number from 1 - 4, 2 is in progress 4 is feedback\
        :param assign_to_id: ID number of the user you want to assign the issue to
        """
        url = urljoin(self.url, 'issues/%s.json' % str(issue_id))
        data = {
            "issue": {
            }
        }
        if status_change is not None:
            data['issue']['status_id'] = status_change

        if assign_to_id is not None:
            data['issue']['assigned_to_id'] = str(assign_to_id)

        if notes is not None:
            data['issue']['notes'] = notes

        self.__put_request_timeout(url, data)

    @staticmethod
    def __url_validator(url):
        from urllib import parse
        qualifying = ('scheme', 'netloc')
        token = parse.urlparse(str(url))
        return all([getattr(token, qualifying_attr)
                    for qualifying_attr in qualifying])

    def __get_request_timeout(self, url):
        import json
        import time

        headers = {'X-Redmine-API-Key': self.api_key}
        self.logger.info("Sending GET request to %s" % url)
        resp = requests.get(url, headers=headers)
        tries = 0
        while resp.status_code != 200 and tries < 10:
            if resp.status_code == 401:  # Unauthorized
                self.logger.info("Invalid Redmine api key!")
                print(resp.content.decode('utf-8'))
                raise RedmineConnectionError("Invalid Redmine api key")

            self.logger.warning("GET request returned status code %d, with message %s. Waiting %ds to retry."
                          % (resp.status_code, resp.content.decode('utf-8'), self.wait))
            time.sleep(self.wait)
            self.logger.info("Retrying...")
            resp = requests.get(url, headers=headers)
            tries += 1
        if tries >= 10:
            raise RedmineConnectionError("Could not connect to redmine servers. Status code %d, message:\n%s"
                                         % (resp.status_code, resp.content.decode('utf-8')))
        else:
            return json.loads(resp.content.decode("utf-8"))

    def __put_request_timeout(self, url, data):
        import time

        self.wait = 60

        self.logger.info("Sending PUT request to %s" % url)

        headers = {'X-Redmine-API-Key': self.api_key, 'content-type': 'application/json'}
        resp = requests.put(url, headers=headers, json=data)
        tries = 0
        while (resp.status_code != 200 and resp.status_code != 201) and tries < 10:  # OK / Created
            self.logger.warning("PUT request returned status code %d, with message %s. Waiting %ds to retry."
                              % (resp.status_code, resp.content.decode('utf-8'), self.wait))
            time.sleep(self.wait)
            self.logger.warning("Retrying...")
            resp = requests.put(url, headers=headers, json=data)
            tries += 1

        if tries >= 10:
            raise RedmineConnectionError("Could not connect to redmine servers. Status code %d, message:\n%s"
                                         % (resp.status_code, resp.content.decode('utf-8')))
        else:
            return resp.status_code


class RedmineConnectionError(ValueError):
    """Raised when there is a problem connecting to redmine"""

    def __init__(self, message, *args):
        self.message = message  # without this you may get DeprecationWarning
        # allow users initialize misc. arguments as any other builtin Error
        super(RedmineConnectionError, self).__init__(message, *args)


class RedmineUploadError(ValueError):
    """Raised when there is a problem uploading redmine file"""

    def __init__(self, message, *args):
        self.message = message  # without this you may get DeprecationWarning
        # allow users initialize misc. arguments as any other builtin Error
        super(RedmineUploadError, self).__init__(message, *args)

# if __name__ == '__main__':
#     RedmineInterface('https://redmine.ca', 'test_key')
