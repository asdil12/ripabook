#!/usr/bin/python2

import os, popen2, string, re, sys
from fcntl import ioctl
import CDROM

class CD(object):
	status_map = {
		CDROM.CDS_DISC_OK: 'READY',
		CDROM.CDS_DRIVE_NOT_READY: 'NOT READY',
		CDROM.CDS_TRAY_OPEN: 'TRAY OPEN',
		CDROM.CDS_NO_DISC: 'NO DISK',
		CDROM.CDS_NO_INFO: 'NO INFO'
	}

	class NotReady(Exception):
		pass

	def __init__(self, drive='/dev/cdrom'):
		self.drive = drive

	def _cdparanoia_args(self, args):
		retargs = ['cdparanoia', '-d', self.drive]
		retargs.extend(args)
		return retargs

	def _run_cmd(self, cmd):
		"""
			Runs the specified command and waits for return.
		"""
		pid = os.fork()
		if pid == 0:
			os.execvp(cmd[0], cmd)
			sys.exit(0)
		proc, ret = os.waitpid(pid, 0)
		if ret:
			raise Exception("'%s' returned %d" % (cmd.join(' '), ret))

	def _run_cmd_out(self, cmd):
		"""
			Runs the specified command and returns output: (stdout, stderr)
		"""
		child_stdout, child_stdin, child_stderr = popen2.popen3(cmd)
		ret_stdout = []
		ret_stderr = []
		try:
			for f in map(string.strip, child_stdout.readlines()):
				ret_stdout.append(f)
		except:
			pass
		try:
			for f in map(string.strip, child_stderr.readlines()):
				ret_stderr.append(f)
		except:
			pass
		child_stdin.close()
		child_stdout.close()
		child_stderr.close()
		return ret_stdout, ret_stderr

	def _cd_ioctl(self, cmd):
		"""
			Runs ioctl on cd drive and returns output
		"""
		fd = os.fdopen(os.open(self.drive, os.O_RDONLY | os.O_NONBLOCK))
		if cmd == CDROM.CDROMEJECT:
			ioctl(fd, CDROM.CDROM_LOCKDOOR, 0)
		return ioctl(fd, cmd)

	def _ensure_ready(self):
		"""
			Raises if not ready
		"""
		status = self._cd_ioctl(CDROM.CDROM_DRIVE_STATUS)
		if status == CDROM.CDS_DISC_OK:
			return True
		else:
			raise CD.NotReady("Got state '%s'" % CD.status_map[status])

	@property
	def tray_open(self, set=None):
		"""
			Returns tray status
		"""
		return self._cd_ioctl(CDROM.CDROM_DRIVE_STATUS) == CDROM.CDS_TRAY_OPEN

	@tray_open.setter
	def tray_open(self, value):
		"""
			Set tray
		"""
		cmd = CDROM.CDROMEJECT if value else CDROM.CDROMCLOSETRAY
		self._cd_ioctl(cmd)

	@property
	def empty(self):
		"""
			Returns True if tray is empty
		"""
		return self._cd_ioctl(CDROM.CDROM_DRIVE_STATUS) == CDROM.CDS_NO_DISC

	@property
	def ready(self):
		"""
			Returns True if drive is ready
		"""
		return self._cd_ioctl(CDROM.CDROM_DRIVE_STATUS) == CDROM.CDS_DISC_OK

	@property
	def tracks(self):
		"""
			Returns a list with the track numbers
		"""
		self._ensure_ready()
		ret = []
		exp = re.compile("\d+\.")
		for f in self._run_cmd_out(self._cdparanoia_args(['-Q']))[1]:
			res = exp.match(f)
			if res:
				ret.append(int(f.split(".")[0]))
		return ret

	def ripp(self, track, outfile='tmp.wav'):
		"""
			Ripp a track
		"""
		self._ensure_ready()
		if track not in self.tracks:
			raise ValueError("Can't find requested track %d in %s" % (track, self.tracks))
		self._run_cmd(self._cdparanoia_args([str(track), outfile]))
