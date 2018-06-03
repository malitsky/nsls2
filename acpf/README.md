## Archiver Configuration Python Frontend Test Environment  

The Archiver Configuration Python Frontend (ACPF) is developed for extending
the scope of the [EPICS Archiver Appliance](https://slacmshankar.github.io/epicsarchiver_docs/)
WebUI interface with a collection of methods for
registering numerous PVs from different NSLS-II sub-systems. Its usage can
be illustrated with the [demo](https://github.com/malitsky/nsls2/blob/master/acpf/acpf-demo.6.01.2018.ipynb)
conducted on the gpu-001 test environment.

### Creating the ACPF instance

ACPF methods are consolidated as an ArchiverConfig class that relies on standard Python
modules for communicating with the HTTP servers. As a result, the ArchiverConfig implementation
is encapsulated in a single acpf.py file and can be directly imported without an additional
deployment procedure.

```python
from acpf import ArchiverConfig
```

To create the ArchiverConfig instance, it needs to have a specified address of the EPICS Archiver
Appliance MGMT service. In NSLS-II, each beamline maintaines its own archiver on a dedicated
server. The corresponding address is defined in the /etc/archappl/appliances.xml file.
The demo is demonstrated within the context of the xf04id beamline:

```python
bpl_url = 'http://xf04id-ca1.cs.nsls2.local:17665/mgmt/bpl'
arconf = ArchiverConfig(bpl_url)
```
### Retrieving PVs from the EPICS Archiver Appliance

ACPF communication with the EPICS Archiver Appliance is based on a set of 
[business logic commands](https://slacmshankar.github.io/epicsarchiver_docs/api/mgmt_scriptables.html)
supported by the MGMT service. One of them is *getAllPV* for retrieving all PVs from the archiver.
The command has two optional arguments: regex and limit. The *regex* argument can contain
a [Java regex](https://docs.oracle.com/javase/7/docs/api/java/util/regex/Pattern.html)
wildcard. The *limit* argument specifies the number of matched PVs that are returned.
If unspecified, the method returns 500 PV names. 

```python
all_pvs = arconf.getAllPVs(limit = 10000)
```

### Retrieving PVs from the Channel Finder 

In addition to the Archiver Appliance business logic commands, the ArchiverConfig class provides access
to the [EPICS Channel Finder](http://channelfinder.github.io/), a directory service for EPICS channels.
The ACPF interface follows the NSLS-II Standard-Naming Convention defining the PV names in the form
*System{Device}Signal*. For this example, the demo selects all PVs with `'.*Mtr.*StringOut_'` signals:

```python
bl = "xf04"
new_pvs = arconf.selectNewPVs(bl, system = '', device = '.*', signal = '.*Mtr.*StringOut_')
```

### Selecting PVs for Archiving

After retrieving two PV collections from Archiver and Channel Finder in the same Python script,
their difference can be compared, analyzed, and selected using standard Python methods.
The demo selects 1000 PVs from the difference of the two collections:

```python
diff_pvs = list(set(new_pvs) - set(all_pvs))
demo_pvs = diff_pvs[0:1000]
```

### Archiving PVs

In the EPICS Archiver Appliance, the PV registration is a complex procedure requiring several minutes
for processing multiple steps. The corresponding request however is asynchroneous.
Therefore, the demo adds a 5-minute time delay for processing 1000 PVs:

```python
archive_pvs = arconf.archivePV(demo_pvs)
time.sleep(300)
```

The status of a request can be checked with the *getArchivingStatus* command. 
The present Archiver Appliance can handle a subset of PVs. Therefore, requests of
unarchived PVs need to be aborted:

```python
archived, others = arconf.getArchivingStatus(demo_pvs)
for i, pv in enumerate(others, start=1):
    arconf.abortArchivingPV(pv)
```

### Restoring the Original Test Configuration

In order to return back to the initial test configuration, archived PVs need
to be deleted. In the EPICS Archiver Appliance, the deleting procedure requires
to preliminary pause the corresponding PVs. This method is also asynchroneous
and requires a time delay. For controling this procedure, the test demo applies
an additional *getPausedPVsReport* method:


```python
paused_pvs_1 = arconf.getPausedPVsReport()
pause_pvs = arconf.pauseArchivingPV(archived)
time.sleep(30)
paused_pvs_2= arconf.getPausedPVsReport()
```

Finally, paused PVs can be deleted and the status of the test configuration is checked
with the *getPausedPVsReport* and *getAllPVs* methods:

```python
for i, pv in enumerate(archived):
    delete_pv = arconf.deletePV(pv)
paused_pvs = arconf.getPausedPVsReport()
final_pvs = arconf.getAllPVs(limit = 10000)
```