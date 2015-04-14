import subprocess, os, signal, shlex, time
from flask import url_for
from datetime import datetime
    
#runqueue is executed on seperate thread
#flask server imports this file, always uses queueup
import model

class JobRunner(object):
    def __init__(self, filearg=None):
        self.filearg = filearg
        
        #get the directory of where the queue is
        self.datastore = model.FileSystemStore()
        self.queuedir = self.datastore.QUEUEDIR
        
        #whoami?
        self.whoami = '172.20.4.60'

    def runJob(self, jobID=None, filearg=None):
        #if filearg is set from an internal function, i.e. runQueue
        #make sure to set self.filearg so it can be used later
        print 'attempting to run job: ' + str(jobID)
        if filearg:
            self.filearg = filearg

        cmd = 'tsung -f ' + self.filearg + ' start'
        cmd = cmd.encode('utf8')
        args = shlex.split(cmd)
        
        self.process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE)

        rc = self.process.returncode
        if rc != None or rc != 0:
            #write error to a file to be picked up by getstatus
            #json - error: unable to start job
            #detail: tsung error, capture stdout
            print 'rc = None or rc != 0'

        while True:
            data = self.process.stdout.readline()   # Alternatively proc.stdout.read(1024)
            if len(data) == 0:
                break
            #sample output below
            #"Log directory is: /home/andrewgerhold/.tsung/log/20140204-1203"
            if "Log directory" in data:
                self.logdir = str(data)[18:-1]
                print 'log dir from stdout: ' + self.logdir
                break

        if self.logdir == None:
            #write error to a file to be picked up by getstatus
            #json - error: unable to start job
            #detail: tsung error, capture stdout
            pass            

        newjobmodel = model.FileSystemStore(jobID=jobID)
        newjobmodel.updateToRunning(self.process.pid, self.logdir)

        #print 'Wait until process is done...and check for running'

        self.process.wait()

        #there is a " at the end and a space at the start of self.logdir
        self.logdir = self.logdir.replace("\"", "").strip()

        #logdir = os.path.expanduser('~/.tsung/log/'+self.logdir)
        # print 'expanduser result: ' + logdir
        
        if not os.path.exists(self.logdir):
            #todo: raise exception
            print "path doesn't exist: " + self.logdir
        else:
            print "path exists! : " + self.logdir
            resultsdir = self.queuedir + jobID + '/' + 'results'
            print 'attempting to move to: ' + resultsdir
            os.rename(self.logdir, resultsdir)
            if os.path.exists(resultsdir):
                print 'move successful!'
            else:
                print 'move failed'

        process = subprocess.Popen('/usr/lib/tsung/bin/tsung_stats.pl', shell=False, cwd=resultsdir)

        self.process.wait()

        newjobmodel.updateToCompleted()

        print 'completed: ' + jobID

    def runQueue(self):
        #todo: refactor this function
        #A directory must contain a file called queued
        #and a xml file in order to be ran successfully
        jobID = None
        xmlfile = None

        #run all the time, maybe sleep for a second?
        while True:
            i = datetime.now()
            print i.strftime('%Y/%m/%d %H:%M:%S') + " all the files and dirs checked, waiting for 5 seconds"
            time.sleep(5)
            for root, dirs, files in os.walk(self.queuedir):
                for file in files:
                    #check for a file called 'queued'
                    if file == 'queued':
                        #todo: check resources, if available
                        print "checking job: " + str(os.path.basename(root))
                        #how to: where basename for '/foo/bar/' returns 'bar'
                        jobID = str(os.path.basename(root))

                    #check for a file ending in '.xml'
                    if '.xml' in file:
                        xmlfile = file

                #if both exist in this directory, then attempt to run the job
                if xmlfile and jobID:
                    print 'running job: ' + jobID + ' with file: ' + xmlfile
                    filearg = os.path.join(self.queuedir, jobID, xmlfile)
                    self.runJob(filearg=filearg, jobID=jobID)
                else:
                    #both do no exist, since we are
                    #going to the next directory
                    #reset the flags
                    jobID = None
                    xmlfile = None

                #this can be removed, once the above code is refactored
                #it is currently just a failsafe
                jobID = None
                xmlfile = None
            
            #this is to reset the variables 
            #in the while true loop for the next run
            jobID = None
            xmlfile = None

    def queueJob(self):
        #create a jobID, make a jobID directory, and store the valid jobID
        jobData = model.FileSystemStore()
        jobID = jobData.updateToQueued()
        
        #move the file from /uploads to the root of its new JobID directory
        xmlfilename = self.filearg[7:]
        os.rename(self.filearg, self.queuedir + str(jobID) + '/' + xmlfilename)

        return jobID

    def abortJob(self, jobID=None):
        #todo: refactor after understanding more about
        #killing individual pids. research has shown that
        #the bash process that started all the tsung beams
        #is not the parent of these processes, so killing it
        #does not terminate any tsung processes.

        #it might be possible to serialize an subprocess object
        #and then access its methods and kill the process this way.
        #as when the process is killed using the original subprocess
        #class, it terminates successfully

        #note that SIGKILL is used below and
        #if SIGTERM is used, the char 'a' must be sent to stdin
        #to issue an 'abort' as the erlang interpeter 
        #will write to stdout and ask what to do
        
        #DEBUG print "attempting to abort job: "

        task = self.queuedir + jobID
        if not os.path.exists(task):
            raise Exception("jobID doesn't exist")
        
        pidFileToRead = self.queuedir + jobID + '/pid'
        if not os.path.isfile(pidFileToRead):
            raise Exception("pid file doesn't exist")

        with open(pidFileToRead, 'r') as f:
            pid = f.readline()

        #DEBUG print "got the pid: " + str(pid)

        #since kill/terminate by pid doesn't work at this time,
        #as a stop gap that needs refactoring,
        #we are just going to kill by name
        if os.path.isfile(task + '/running'):
            try:
                #just kill any tsung beam by name
                os.system("pkill 'beam'")
            except Exception, e:
                print str(e)

        #update status to aborted
        thisJob = model.FileSystemStore(jobID)
        thisJob.updateToAborted()

    def getstatus(self, jobID=None):
        print "running getstatus..."
        #a list of the valid status'
        status = ['queued','running','aborted','completed']
        #in case jobID = None, create a tasks list to 
        #be returned with all the tasks
        tasks = []

        #initialize task to None to avoid a UnboundLocalError
        task = None

        #if jobID is set, then we are just looking
        #for an individual job
        if jobID:
            print "on a specific job..."
            jobDir = self.queuedir + jobID + "/"
            for root, dirs, files in os.walk(jobDir):
                for file in files:
                    if file in status:
                        filestatus = str(file)
                        #pretty simple eh?
                        return filestatus
        #otherwise, return status' on all the jobs
        else:
            print "on all jobs..."
            print "in queue dir..." + self.queuedir
            for root, dirs, files in os.walk(self.queuedir):
                print "dirs..." + str(dirs)
                for file in files:
                    jobID = str(os.path.basename(root))
                    print "attempting to get status information for..." + jobID
                    if str(file) in status:
                        filestatus = str(file)
                        print 'returing info for: ' + jobID
                        #if the status indicates 
                        if filestatus == 'completed':
                            resultsdir = self.queuedir + jobID + '/results'
                            print 'resultsdir: ' + resultsdir
                            if not os.path.isdir(resultsdir):
                                print 'resultsdir: ' + resultsdir + ' is not a directory!'
                            else:
                                #todo: here I'm cutting out the /tmp directory as nginx only opens queue
                                #I need to configure nginx and refactor this code to match that
                                url = 'http://' + self.whoami + '/' + resultsdir[5:]
                                dtm = datetime.strptime(time.ctime(os.path.getmtime(self.queuedir + jobID + '/' + file)), "%a %b %d %H:%M:%S %Y")
                                #datemodified = time.ctime(os.path.getmtime(self.queuedir + jobID + '/' + file))
                                dtm = dtm.strftime('%Y/%m/%d %H:%M:%S')
                                datemodified = dtm
                                task = {'jobid': jobID, 'status': filestatus, 'url': url, 'datemodified': datemodified}
                                #task = {'jobid': jobID, 'status': filestatus, 'url': resultsdir}
                        else:
                            datemodified = time.ctime(os.path.getmtime(self.queuedir + jobID + '/' + file))
                            task = {'jobid': jobID, 'status': filestatus, 'datemodified': datemodified}
                        
                        tasks.append(task)
        return tasks

if __name__ == "__main__":
    NewJobRunner = JobRunner()
    NewJobRunner.runQueue()
