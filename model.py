import os, uuid, signal

class FileSystemStore(object):
    def __init__(self, jobID=None, logdir=None):
        #set where the fileio storage system will go
        self.LOGDIR = logdir
        self.QUEUEDIR = '/tmp/queue/'
        self.jobID = jobID
        #check if dir exists before using it
        if not os.path.exists(self.QUEUEDIR):
            raise Exception('queue directory not there')

        self.pathToJob = None

        #DEBUG print 'fileio on: ' + str(self.jobID)

        if self.jobID:
            #DEBUG print 'jobID set'
            self.pathToJob = self.QUEUEDIR + str(self.jobID) + '/'
            #DEBUG print 'path: ' + self.pathToJob
            if not os.path.exists(self.pathToJob):
                raise Exception('this jobID does not exist')

    def updateToRunning(self, pid, logdir):
        #global tasks
        #update to completed
        if self.pathToJob:
            #DEBUG print 'updating job: ' + str(self.jobID)
            #DEBUG print 'located at: ' + self.pathToJob
            os.rename(self.pathToJob + 'queued', self.pathToJob + 'running')
            #write pid file
            fileToWrite = self.pathToJob + 'pid'
            #DEBUG print 'writing pid: ' + str(pid) + ' to: ' + fileToWrite
            f = open(fileToWrite, 'w')
            f.write(str(pid) + '\n')
            f.close()
            #write logdir file
            fileToWrite = self.pathToJob + 'logdir'
            print 'writing captured logdir: ' + str(logdir)
            print 'to this file: ' + fileToWrite
            f = open(fileToWrite, 'w')
            f.write(str(fileToWrite) + '\n')
            f.close()

    def updateToCompleted(self):
        #update to completed
        #DEBUG print 'updating job: ' + str(self.jobID)
        #DEBUG print 'located at: ' + self.pathToJob
        if self.pathToJob:
            os.rename(self.pathToJob + 'running', self.pathToJob + 'completed')
            #remove PID
            os.remove(self.pathToJob + 'pid')

    def updateToAborted(self):
        #udpate to aborted
        if self.pathToJob:
            if os.path.isfile(self.pathToJob + 'running'):
                os.rename(self.pathToJob + 'running', self.pathToJob + 'aborted')
            elif os.path.isfile(self.pathToJob + 'queued'):
                os.rename(self.pathToJob + 'queued', self.pathToJob + 'aborted')

    def updateToQueued(self):
        #make jobID
        jobID = uuid.uuid4()
        #mkdir with jobID
        newDir = self.QUEUEDIR + str(jobID)
        os.mkdir(newDir)
        #give status of queued
        fileToWrite = newDir + '/' + 'queued'
        f = open(fileToWrite, 'w')
        f.close()
        #return jobID
        return jobID

    def jobstatus(self, jobID):
        #recurse through directory
        #find job
        #if: 
        #PID, running
        #Abort, aborted
        #No Pid or Abort, Completed (return results instead?)
        pass
