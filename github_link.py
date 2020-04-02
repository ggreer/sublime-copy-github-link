import sublime, sublime_plugin

import os
import re
import subprocess


class CopyGithubLinkCommand(sublime_plugin.TextCommand):
    def run_git(self, cmd, cwd):
        print(cmd, cwd)
        try:
            p = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=cwd)
            result = p.communicate()
            output = result[0].decode('utf-8').strip()
            print('output: %s' % output)
        except Exception as e:
            print('Error running %s: %s' % (cmd, e))
            return
        return output


    def get_repo_url(self):
        filename = self.view.file_name()
        if not filename or len(filename) == 0:
            return
        remote = self.run_git(['git', 'config', '--get', 'remote.origin.url'], os.path.dirname(filename))
        if not remote:
            return
        if remote[:4] == 'git@':
            # ssh remote. transform to https
            p = re.compile('^git@(?P<host>[^:]+):(?P<path>.*)$')
            m = p.match(remote)
            if not m:
                print('Unable to parse remote url %s' % remote)
                return
            host = m.group('host')
            path = m.group('path')
            remote = 'https://%s/%s' % (host, path)
        print('parsed remote %s' % remote)
        if remote[-4:] == '.git':
            remote = remote[:-4]
        return remote
  

    def run(self, edit):
        filename = self.view.file_name()
        if len(filename) == 0:
            sublime.status_message('Can\'t copy: No filename for view.')
            return

        dirname = os.path.dirname(filename)
        branchname = self.run_git(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], dirname)
        project_dir = self.run_git(['git', 'rev-parse', '--show-toplevel'], dirname)
        relpath = self.run_git(['git', 'ls-files', '--error-unmatch', filename], project_dir)
        if not relpath:
            sublime.status_message("File is not tracked in git.")
            return
        repo_url = self.get_repo_url()
        if not repo_url:
            sublime.status_message("Error: No remote url for project")
            return
        url = '%s/blob/%s/%s' % (repo_url, branchname, relpath) # todo: line number
        regions = self.view.sel()
        if len(regions) > 0:
            line, col = self.view.rowcol(regions[0].begin())
            print('LINE', line)
            url += '#L%s' % (line + 1)
        print('url: %s' % url)
        sublime.set_clipboard(url)
        sublime.status_message("Copied Github link")


    def is_enabled(self):
        if not self.get_repo_url():
            return false

        filename = self.view.file_name()
        dirname = os.path.dirname(filename)
        project_dir = self.run_git(['git', 'rev-parse', '--show-toplevel'], dirname)
        relpath = self.run_git(['git', 'ls-files', '--error-unmatch', filename], project_dir)
        return bool(relpath)
