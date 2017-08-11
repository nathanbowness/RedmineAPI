class Issue:
    def __init__(self, issue_dict):
        """
        Creates a Issue class with variable to be called by name rather than with dictionary look ups
        **Can be extended
        :param issue_dict: dictionary with all information about the redmine issue being processed
        """
        self.in_progress_msg = ""
        self.success_msg = ""
        self.error_msg = ""

        self.subject = issue_dict['subject']
        self.id = issue_dict['id']
        self.description = issue_dict['description']

        self.author = issue_dict['author']
        self.author_id = self.author['id']
        self.author_name = self.author['name']
