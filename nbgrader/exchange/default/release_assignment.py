import os
import shutil
import glob
import re
from stat import (
    S_IRUSR, S_IWUSR, S_IXUSR,
    S_IRGRP, S_IWGRP, S_IXGRP,
    S_IROTH, S_IWOTH, S_IXOTH,
    S_ISGID, ST_MODE
)


from nbgrader.exchange.abc import ExchangeReleaseAssignment as ABCExchangeReleaseAssignment
from nbgrader.exchange.default import Exchange


class ExchangeReleaseAssignment(Exchange, ABCExchangeReleaseAssignment):

    def _load_config(self, cfg, **kwargs):
        if 'ExchangeRelease' in cfg:
            self.log.warning(
                "Use ExchangeReleaseAssignment in config, not ExchangeRelease. Outdated config:\n%s",
                '\n'.join(
                    'ExchangeRelease.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.ExchangeRelease.items()
                )
            )
            cfg.ExchangeReleaseAssignment.merge(cfg.ExchangeRelease)
            del cfg.ExchangeRelease

        super(ExchangeReleaseAssignment, self)._load_config(cfg, **kwargs)

    def ensure_root(self):
        perms = S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IWGRP|S_IXGRP|S_IROTH|S_IWOTH|S_IXOTH|((S_IWGRP|S_ISGID) if self.coursedir.groupshared else 0)

        # if root doesn't exist, create it and set permissions
        if not os.path.exists(self.root):
            self.log.warning("Creating exchange directory: {}".format(self.root))
            try:
                os.makedirs(self.root)
                os.chmod(self.root, perms)
            except PermissionError:
                self.fail("Could not create {}, permission denied.".format(self.root))

        else:
            old_perms = oct(os.stat(self.root)[ST_MODE] & 0o777)
            new_perms = oct(perms & 0o777)
            if old_perms != new_perms:
                self.log.warning(
                    "Permissions for exchange directory ({}) are invalid, changing them from {} to {}".format(
                        self.root, old_perms, new_perms))
                try:
                    os.chmod(self.root, perms)
                except PermissionError:
                    self.fail("Could not change permissions of {}, permission denied.".format(self.root))


    @property
    def randomized_assignment(self):
        randomize_indicator_path = os.path.join(
            self.coursedir.format_path(self.coursedir.release_directory, '.', self.coursedir.assignment_id), 
            ".randomized_assignment"
        )
        return os.path.exists()

    def init_src(self):
        self.src_path = self.coursedir.format_path(self.coursedir.release_directory, '.', self.coursedir.assignment_id)
        if not os.path.isdir(self.src_path):
            source = self.coursedir.format_path(self.coursedir.source_directory, '.', self.coursedir.assignment_id)
            if os.path.isdir(source):
                # Looks like the instructor forgot to assign
                self.fail("Assignment found in '{}' but not '{}', run `nbgrader generate_assignment` first.".format(
                    source, self.src_path))
            else:
                self._assignment_not_found(
                    self.src_path,
                    self.coursedir.format_path(self.coursedir.release_directory, '.', '*'))
        
        
        # assignment_generated = True


        # if not self.randomized_assignment:
        #     self.src_path = self.coursedir.format_path(self.coursedir.release_directory, '.', self.coursedir.assignment_id)
        #     if not os.path.isdir(self.src_path):
        #         assignment_generated = False

        #     self.release_dirs = []
                
        # else:
        #     self.src_path = self.coursedir.format_path(
        #         self.coursedir.release_directory, '*',
        #         self.coursedir.assignment_id)

        #     self.release_dirs = glob.glob(self.src_path)

        #     if len(self.release_dirs) == 0:
        #         assignment_generated = False

        # if not assignment_generated:
        #     source = self.coursedir.format_path(self.coursedir.source_directory, '.', self.coursedir.assignment_id)
        #     if os.path.isdir(source):
        #         # Looks like the instructor forgot to assign
        #         self.fail("Assignment found in '{}' but not '{}', run `nbgrader generate_assignment` first.".format(
        #             source, self.src_path))
        #     else:
        #         self._assignment_not_found(
        #             self.src_path,
        #             self.coursedir.format_path(self.coursedir.release_directory, '.', '*'))

    def init_dest(self):
        if self.coursedir.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.course_path = os.path.join(self.root, self.coursedir.course_id)
        self.outbound_path = os.path.join(self.course_path, 'outbound')
        self.inbound_path = os.path.join(self.course_path, 'inbound')
        self.dest_path = os.path.join(self.outbound_path)
        # 0755
        # groupshared: +2040
        self.ensure_directory(
            self.course_path,
            S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH|((S_ISGID|S_IWGRP) if self.coursedir.groupshared else 0)
        )
        # 0755
        # groupshared: +2040
        self.ensure_directory(
            self.outbound_path,
            S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH|((S_ISGID|S_IWGRP) if self.coursedir.groupshared else 0)
        )
        # 0733 with set GID so student submission will have the instructors group
        # groupshared: +0040
        self.ensure_directory(
            self.inbound_path,
            S_ISGID|S_IRUSR|S_IWUSR|S_IXUSR|S_IWGRP|S_IXGRP|S_IWOTH|S_IXOTH|(S_IRGRP if self.coursedir.groupshared else 0)
        )

    def copy_files(self):
        randomize_indicator_path = os.path.join(
            self.coursedir.release_directory, self.coursedir.assignment_id, ".randomized_assignment"
        )

        if not os.path.exists(randomize_indicator_path):
            dest_path = self.coursedir.format_path(
                self.dest_path, '.', self.coursedir.assignment_id
            )

            if os.path.isdir(dest_path):
                if self.force:
                    self.log.info("Overwriting files: {} {}".format(
                        self.coursedir.course_id, self.coursedir.assignment_id
                    ))
                    shutil.rmtree(dest_path)
                else:
                    self.fail("Destination already exists, add --force to overwrite: {} {}".format(
                        self.coursedir.course_id, self.coursedir.assignment_id
                    ))
        
            self.log.info("Source: {}".format(self.src_path))
            self.log.info("Destination: {}".format(dest_path))
            self.do_copy(self.src_path, dest_path)
            self.set_perms(
                dest_path,
                fileperms=(S_IRUSR|S_IWUSR|S_IRGRP|S_IROTH|(S_IWGRP if self.coursedir.groupshared else 0)),
                dirperms=(S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH|((S_ISGID|S_IWGRP) if self.coursedir.groupshared else 0)))
            self.log.info("Released as: {} {}".format(self.coursedir.course_id, self.coursedir.assignment_id))

        else:
            if self.coursedir.student_id_exclude:
                exclude_students = set(self.coursedir.student_id_exclude.split(','))
            else:
                exclude_students = set()

            # Copy randomized indicator file
            src_path = os.path.join(self.src_path, ".randomized_assignment")

            dest_dir = os.path.join(self.dest_path, self.coursedir.assignment_id)
            if not os.path.exists(dest_dir):
                os.mkdir(dest_dir)
            dest_path = os.path.join(dest_dir, ".randomized_assignment")
            shutil.copyfile(src_path, dest_path)
                
            # Copy notebooks
            for student_id in os.listdir(self.src_path):
                src_path = os.path.join(self.src_path, student_id)

                # If not a directory skip
                if not os.path.isdir(src_path):
                    continue

                if student_id in exclude_students:
                    self.log.debug("Skipping student '{}'".format(student_id))
                    continue

                dest_path = self.coursedir.format_path(
                    self.dest_path, self.coursedir.assignment_id, student_id
                )

                self.do_copy(src_path, dest_path)
                self.set_perms(
                    dest_path,
                    fileperms=(S_IRUSR|S_IWUSR|S_IRGRP|S_IROTH|(S_IWGRP if self.coursedir.groupshared else 0)),
                    dirperms=(S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH|((S_ISGID|S_IWGRP) if self.coursedir.groupshared else 0)))

            self.log.info("Released as: {} {}".format(self.coursedir.course_id, self.coursedir.assignment_id))

                
