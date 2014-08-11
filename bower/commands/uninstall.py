import sublime
import sublime_plugin
import json
import os

try:
    # ST3
    from ..utils.cli import CLI
except ImportError:
    # ST2
    from bower.utils.cli import CLI


class UninstallCommand(sublime_plugin.WindowCommand):

    def config_path(self):
        # TODO: Maybe this function should be refactored into an util,
        # it is repeated in many classes
        try:
            project_file_path = self.window.project_file_name()
            return os.path.dirname(project_file_path)
        except AttributeError:
            return self.window.folders()[0]

    def run(self, *args, **kwargs):
        self.list_installed_packages()

    def list_installed_packages(self):
        command = ['list', '-p', '--json']
        results = CLI().execute(command, cwd=self.config_path())
        results = json.loads(results)
        self.packages = [package for package in results]
        if self.packages:
            self.window.show_quick_panel(self.packages, self.uninstall_package)
        else:
            sublime.status_message('No packages left to uninstall.')

    def uninstall_package(self, index, force=False):
        if (index == -1):
            return  # user didn't select anything

        name = self.packages[index]
        command = ['uninstall', '--save', name]
        if force:
            command.append('--force')

        results = CLI().execute(command, cwd=self.config_path())

        if 'uninstall' in results:  # success
            sublime.status_message("{0} successfully uninstalled".format(name))
            # timeout hack necessary to show list again
            sublime.set_timeout(self.list_installed_packages, 0)
        elif 'depends' in results:  # dependency
            message = results.split('ECONFLICT')[-1].strip().capitalize()
            message += '. Uninstall {0} anyway?'.format(name)
            if sublime.ok_cancel_dialog(message, 'Yes'):
                self.uninstall_package(index, force=True)
            else:
                sublime.set_timeout(self.list_installed_packages, 0)
