import os
import datetime
from . pyaccessories.TimeLog import Timer


class Values:
    """
    Generic default values used to validate and run Redmine Automation processes
    """

    # default values
    nas_mount_path = "/mnt/nas/"
    check_time = 600
    first_run = 'yes'

    # Normal Keys
    responded_issues = 'responded_issues'
    encryption_key = 'Sixteen byte key'


class Keys:
    """
    Default keys to be stored and accessed from the config file
    """

    # Config Json Keys
    redmine_api_key = 'redmine_api_key_encrypted'
    first_run = 'first_run'
    secs_between_checks = 'secs_between_redmine_checks'
    nas_mount = 'nasmnt'


class FileExtension:
    """
    Default file extensions to be used when tracking progress and logging runs
    """
    # Path or extensions (extn)
    config_json = 'config.json'
    runner_log = 'runner_logs'
    issues_json = 'responded_issues.json'


def create_timerlog(basepath, path_ext):
    return Timer(log_file=os.path.join(basepath, path_ext,
                                       datetime.datetime.now().strftime("%d-%m-%Y_%H:%M:%S")))


def get_validated_seqids(sequences_list):

    validated_sequence_list = list()
    regex = r'^(2\d{3}-\w{2,10}-\d{3,4})$'
    import re
    for sequence in sequences_list:
        if re.match(regex, sequence.sample_name):
            validated_sequence_list.append(sequence)
        else:
            raise ValueError("Invalid seq-id \"%s\"" % sequence.sample_name)

    if len(validated_sequence_list) < 1:
        raise ValueError("Invalid format for redmine request. Couldn't find any fastas or fastqs to extract")

    return validated_sequence_list
