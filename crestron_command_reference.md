# Crestron CP4 Command Reference

Auto-generated from `HELP ALL` and `COMMAND ?` queries on a CP4 processor.

**Total commands: 414** | **Documented: 375**

## Command Index

| Command | Role | Description |
|---------|------|-------------|
| [3STONES](#3stones) | Administrator | Test watchdog timer |
| [8021XAUthenticate](#8021xauthenticate) | Administrator | Enable/Disable 802.1x Authentication. |
| [8021XDOMain](#8021xdomain) | Administrator | Configure/View 802.1x Domain Name. |
| [8021XMEThod](#8021xmethod) | Administrator | Configure/View EAP Method. |
| [8021XPASsword](#8021xpassword) | Administrator | Configure 802.1x Password. |
| [8021XSENdpeapver](#8021xsendpeapver) | Administrator | Enable/Disable 802.1x Peap version reporting. |
| [8021XTRUStedcas](#8021xtrustedcas) | Administrator | Select/List 802.1x Trusted CA Certificates |
| [8021XUSERname](#8021xusername) | Administrator | Configure/View 802.1x User Name. |
| [8021XVALidateserver](#8021xvalidateserver) | Administrator | Require Validation Of 802.1x Authentication Server's Certificate. |
| [ADDAUTHDOMain](#addauthdomain) | Administrator | Add authentication domain details |
| [ADDBLOCKEDip](#addblockedip) | Administrator | Add an IP Address to the blocked list |
| [ADDDOMAINGroup](#adddomaingroup) | Administrator | Create a new domain group |
| [ADDDns](#adddns) | Administrator | Add an entry to DNS server List |
| [ADDGroup](#addgroup) | Administrator | Create a new local group |
| [ADDHOSTS](#addhosts) | Administrator | Add hosts entries |
| [ADDLOCKEDUser](#addlockeduser) | Administrator | Add user to the blocked list |
| [ADDMaster](#addmaster) | Programmer | Add a master entry to IP table |
| [ADDPUBKEYTouser](#addpubkeytouser) | Administrator | Add a public key to an existing user account |
| [ADDPeer](#addpeer) | Programmer | Add a peer(slave) entry to IP table |
| [ADDUSER](#adduser) | Administrator | Create a new local user |
| [ADDUSERTogroup](#addusertogroup) | Administrator | Add an existing local or domain user to an existing local group |
| [ADLOGIN](#adlogin) | Administrator | Active Directory Login |
| [ADLOGOUt](#adlogout) | Administrator | Active Directory Logout |
| [APIWEBTOKEN](#apiwebtoken) | Operator | (*) AVF REST api web token |
| [APPSTATs](#appstats) | Operator | Dumps out Registered App Stats |
| [AUCANCEL](#aucancel) | Administrator | Cancel the auto update in progress. |
| [AUCHECKNOW](#auchecknow) | Administrator | Check for updates now. |
| [AUDEVCONNECTPASS](#audevconnectpass) | Administrator | Get/Set the password used by auto update to login to Crestron devices. |
| [AUDEVCONNECTUSER](#audevconnectuser) | Administrator | Get/Set the username used by auto update to login to Crestron devices. |
| [AUDISALLOWDOWNGRADE](#audisallowdowngrade) | Administrator | If ON will not allow Firmware downgrade else allow firmware downgrade. |
| [AUDITLogging](#auditlogging) | Administrator | Display or Change the current audit logging operation. |
| [AUENABLE](#auenable) | Administrator | Enable/disable automatic updates. |
| [AUFORCEUPDATENOW](#auforceupdatenow) | Administrator | Force updates now. |
| [AUMANIFESTURL](#aumanifesturl) | Administrator | Get or Set auto updater manifest URL. |
| [AUPASSWORD](#aupassword) | Administrator | Get/Set the password used by auto update to login to the update server. |
| [AUPEERVERIFY](#aupeerverify) | Administrator | If ON perform peer verification else no peer verification. |
| [AUPLUGINCATALOGURL](#auplugincatalogurl) | Administrator | Get or Set auto updater plugin catalog URL. |
| [AUPOLLINTERVAL](#aupollinterval) | Administrator | Set how long to wait before checking for updates again. |
| [AUSTATUS](#austatus) | Programmer | Reports the auto update status. |
| [AUTHDOMAINMode](#authdomainmode) | Administrator | Display or change authentication domain mode |
| [AUTHentication](#authentication) | Administrator | Authentication on/off |
| [AUTIME](#autime) | Administrator | Set a scheduled time for when to check for updates. |
| [AUTOBRIGHTNESS](#autobrightness) | Programmer | Configure auto-brightness. |
| [AUTODIScovery](#autodiscovery) | Operator | Commands for Ethernet auto discovery |
| [AUTODIScovery](#autodiscovery) | Operator | Commands for Ethernet auto discovery |
| [AUTONegotiate](#autonegotiate) | Administrator | Set Ethernet Auto Negotiation |
| [AUUSERNAME](#auusername) | Administrator | Get/Set the username used by auto update to login to the update server. |
| [AUVERIFYSIGNATURE](#auverifysignature) | Administrator | If ON perform firmware signature verification else no signature verification. |
| [AVFRESTORE](#avfrestore) | Operator | (*) Set the AVF configuration for Factory default |
| [AVFTIMER](#avftimer) | Programmer | (*) avtimer [start|stop] |
| [AVFVER](#avfver) | Operator | (*) Displays AV Framework version |
| [BACNETAUTODiscovery](#bacnetautodiscovery) | Administrator | Disables/enables Auto Discovery for remote devices/objects |
| [BACNETBDT](#bacnetbdt) | Operator | Writes or reads a BACnet Broadcast Distribution Table (BDT) |
| [BACNETDETECTOffline](#bacnetdetectoffline) | Operator | Enables/disables remote device offline detection |
| [BACNETDEVICediscovery](#bacnetdevicediscovery) | Administrator | Starts/stops device discovery |
| [BACNETDEVicescantime](#bacnetdevicescantime) | Administrator | Sets remote device discovery time |
| [BACNETDISPLAYdiscovery](#bacnetdisplaydiscovery) | Administrator | Displays discovery data |
| [BACNETDIsablereadfwrite](#bacnetdisablereadfwrite) | Administrator | Disables/enables the read request followed by write |
| [BACNETENBBMDACCEPtfd](#bacnetenbbmdacceptfd) | Administrator | Enables/disables BBMD Accept FD Registrations functionality |
| [BACNETEnablebbmd](#bacnetenablebbmd) | Administrator | Enables/disables BBMD functionality |
| [BACNETGETCUrrentload](#bacnetgetcurrentload) | Administrator | Displays the stack internal resources usage |
| [BACNETGETMEMusage](#bacnetgetmemusage) | Operator | Gets current and peak memory usage for BACnet Stack... |
| [BACNETGEtobjectcount](#bacnetgetobjectcount) | Operator | Displays BACnet object count |
| [BACNETHOSTCovsupport](#bacnethostcovsupport) | Administrator | Enables/disables COV support for the Host objects |
| [BACNETHostcovlist](#bacnethostcovlist) | Operator | Displays list of COV subscriptions with the Host device |
| [BACNETLIstobjectprop](#bacnetlistobjectprop) | Operator | Lists BACnet device/object properties. |
| [BACNETMAXapdutimeout](#bacnetmaxapdutimeout) | Administrator | Sets maximum APDU Timeout for request retry |
| [BACNETNUmberofretries](#bacnetnumberofretries) | Administrator | Sets the maximum number of retries |
| [BACNETOBJECtdiscovery](#bacnetobjectdiscovery) | Administrator | Starts/stops object discovery of a remote device |
| [BACNETObjectlist](#bacnetobjectlist) | Operator | Lists all BACnet objects configured |
| [BACNETPRIorityforhostwp](#bacnetpriorityforhostwp) | Administrator | Sets the write priority for the hosted objects |
| [BACNETREMOTECOVType](#bacnetremotecovtype) | Administrator | Sets COV type ((Un)Confirmed) for the remote objects |
| [BACNETREMOTEstatuslist](#bacnetremotestatuslist) | Operator | Displays remote devices online/offline status |
| [BACNETREMotecovlist](#bacnetremotecovlist) | Operator | Displays list of Host COV subscriptions with the Remote device |
| [BACNETRegasfd](#bacnetregasfd) | Administrator | Registers Control System As Foreign Device |
| [BACNETSETBIndlimit](#bacnetsetbindlimit) | Administrator | Sets the maximum remote device binding with the host device |
| [BACNETSETDLYBTnwhoisreq](#bacnetsetdlybtnwhoisreq) | Administrator | Sets delay between WhoIs request groups |
| [BACNETSETNEtworknum](#bacnetsetnetworknum) | Administrator | Sets the Network Number |
| [BENCHMARKS](#benchmarks) | Administrator | Run Platform benchmarks |
| [BLUETOOTH](#bluetooth) | Programmer | Configure bluetooth feature |
| [BROADcast](#broadcast) | Operator | Enable Error Broadcast |
| [BTPAN](#btpan) | Programmer | Configure bluetooth PAN feature |
| [BYE](#bye) | Operator | Close user session |
| [CAMDEVICES](#camdevices) | Operator | (*) Camera Device Info |
| [CARDS](#cards) | Operator | Display Cards Detected in System |
| [CCDCLOUDREPORTER](#ccdcloudreporter) | Programmer | (*) Tests cloud registration |
| [CCDINFO](#ccdinfo) | Programmer | (*) Prints out information regarding all the loaded drivers |
| [CCDLOGGING](#ccdlogging) | Programmer | (*) Toggles general logging for the driver |
| [CCDLOGGINGLEVEL](#ccdlogginglevel) | Programmer | (*) Sets the logging level for the driver |
| [CCDRXDEBUG](#ccdrxdebug) | Programmer | (*) Toggles connection transport (RX) logging |
| [CCDSTACKTRACE](#ccdstacktrace) | Programmer | (*) Toggles stack trace printing when exceptions occur |
| [CCDSTATES](#ccdstates) | Programmer | (*) Prints out driver states |
| [CCDTXDEBUG](#ccdtxdebug) | Programmer | (*) Toggles connection transport (TX) logging |
| [CD](#cd) | Operator | Change directory |
| [CERTIFicate](#certificate) | Administrator | Add, Remove, List or View Certificates |
| [CIPPORT](#cipport) | Programmer | Set port number for CIP |
| [CIPTIMESET](#ciptimeset) | Administrator | Enable/Disable setting of time via CIP |
| [CLEARAUDITLOG](#clearauditlog) | Administrator | Clear the audit log. |
| [CLEARCAMERAS](#clearcameras) | Operator | (*) Camera Device Info |
| [CLEARCSAUTHENTICATION](#clearcsauthentication) | Administrator | Clear Control System Authentication credentials. |
| [CLEAREVents](#clearevents) | Administrator | Clear application timer events |
| [CLEAREXTERNALMODules](#clearexternalmodules) | Programmer | Clears the persistent data of external modules. |
| [CLEARLIGHTS](#clearlights) | Operator | (*) Clear Light Configs |
| [CLEARerr](#clearerr) | Operator | Clears the current error log |
| [CLOUDPROXYAUTH](#cloudproxyauth) | Administrator | Sets the authentication method for connecting to a proxy |
| [CLOUDPROXYURL](#cloudproxyurl) | Administrator | Sets the url of the proxy used to make requests |
| [CONFIGUTILS](#configutils) | Administrator | Configuration utilities for data export and import |
| [CONSOLESETMICGAIN2](#consolesetmicgain2) | Operator | (*) MicId, gainValue |
| [COPYfile](#copyfile) | Programmer | Copy a file to a different directory |
| [CORE3XPANELWEB](#core3xpanelweb) | Programmer | Configure the core3 XPanel Flash policy server |
| [COREDUMPSLEEPtime](#coredumpsleeptime) | Operator | Display watchdog coredump sleep time (in seconds) |
| [CREATECsr](#createcsr) | Administrator | Generate a CSR. |
| [CSIODebug](#csiodebug) | Operator | Set/View run-time CSIO debug options. |
| [CSONLINEUPTIME](#csonlineuptime) | Programmer | Get CS online uptime |
| [CSPROJECTRemove](#csprojectremove) | Programmer | Remove the project from Control System |
| [CSPROJECTload](#csprojectload) | Programmer | Load the project in Control System |
| [CWSANTICSRF](#cwsanticsrf) | Administrator | Enables/disables Anti-csrf feature |
| [CWSBASICAUTHentication](#cwsbasicauthentication) | Administrator | Enables/disables CWS Basic Authentication feature |
| [DATASTOREDELete](#datastoredelete) | Programmer | Clear the Logs for the Specified Program |
| [DATASTOREEXPORT](#datastoreexport) | Administrator | Export to XML file |
| [DATASTOREIMPORt](#datastoreimport) | Operator | Import from XML file |
| [DATASTORESTATus](#datastorestatus) | Operator | The Data Store Status |
| [DATASTreamstats](#datastreamstats) | Operator | Printing stream statistics |
| [DBGDEVice](#dbgdevice) | Operator | (*) Simulate incoming packets for the sleected device |
| [DBGMGR](#dbgmgr) | Programmer | Enable/Disable Debug for a given Manager |
| [DBGPKTRX](#dbgpktrx) | Operator | (*) Custom App Rx Debug. |
| [DBGPKTTX](#dbgpkttx) | Operator | (*) Custom App Tx Debug. |
| [DBGSIGnal](#dbgsignal) | Operator | (*) Set/view Debug flags and signal values |
| [DBGTRANSMITTER](#dbgtransmitter) | Operator | (*) Set/Clear IR/RF Transmitter Debug flag |
| [DEBUGPROGram](#debugprogram) | Programmer | Configure debugging for SIMPL# Pro programs. |
| [DEBug](#debug) | Operator | Set/View run-time debug options |
| [DEFRouter](#defrouter) | Administrator | Set default router |
| [DELETEAUTHDOMain](#deleteauthdomain) | Administrator | Delete a configured authentication domain |
| [DELETEDOMAINGroup](#deletedomaingroup) | Administrator | Delete an existing domain group |
| [DELETEGroup](#deletegroup) | Administrator | Delete an existing local group |
| [DELETEUser](#deleteuser) | Administrator | Delete an existing local user |
| [DELete](#delete) | Programmer | Remove File(s) |
| [DHCP](#dhcp) | Administrator | Control dynamic IP addressing |
| [DHCPEx](#dhcpex) | Administrator | Control dynamic IP addressing |
| [DHCPOpt](#dhcpopt) | Administrator | Use FQDN in DHCP Discover Request |
| [DIR](#dir) | Operator | List files and directories in current directory |
| [DISABLEDEFAULTPROGram](#disabledefaultprogram) | Programmer | Get or Set Current DefaultProgram Status |
| [DISABLEREBOOTOFprog0](#disablerebootofprog0) | Operator | Disables repeated reboot of Prog00 |
| [DOMAINNAMEEx](#domainnameex) | Administrator | Set domain name |
| [DOMAinname](#domainname) | Administrator | Set domain name |
| [DUMPCOMCAPS](#dumpcomcaps) | Operator | Dumps comp port HW capabilities |
| [ECHo](#echo) | Operator | Enable/disable character echoing |
| [EDEBUG](#edebug) | Operator | Set/View run-time ethernet debug options |
| [ENABLEFEature](#enablefeature) | Administrator | Enable Disable features |
| [ERASE](#erase) | Programmer | Remove file(s) |
| [ERRlog](#errlog) | Operator | Prints the current error log |
| [FANTest](#fantest) | Operator | fan test; speed/power/params |
| [FGETfile](#fgetfile) | Programmer | FTP file from a remote server |
| [FIPSMode](#fipsmode) | Administrator | Display or change FIPS mode |
| [FORCEDREBOOT](#forcedreboot) | Operator | Forces system reboot |
| [FORMAT](#format) | Operator | Format removeable media |
| [FPUTfile](#fputfile) | Programmer | FTP file to a remote server |
| [FREE](#free) | Operator | Show available file space |
| [GETAUDITLOG](#getauditlog) | Administrator | Retrieve the audit log. |
| [GETCODE](#getcode) | Operator | Retrieve code needed for eControl2 activation |
| [GETIPTABLE](#getiptable) | Operator | Transfer the IP table from Internal flash |
| [GETJOINFROMCRESNEXT](#getjoinfromcresnext) | Programmer | Get Join from CresNext Object |
| [GETMULTISLOTANALOGJOIN](#getmultislotanalogjoin) | Programmer | Get a multi slotted analog join |
| [GETMULTISLOTDIGITALJOIN](#getmultislotdigitaljoin) | Programmer | Get a multi slotted digital join |
| [GETMULTISLOTSERIALJOIN](#getmultislotserialjoin) | Programmer | Get a multi slotted serial join |
| [GETPAsswordrule](#getpasswordrule) | Administrator | Display password rules |
| [HEARTBEATtimeout](#heartbeattimeout) | Administrator | Set TCP Socket Send Timeout value in Milliseconds |
| [HELP](#help) | Operator | Display help screens |
| [HOSTname](#hostname) | Administrator | Set hostname |
| [HWDEVTest](#hwdevtest) | Operator | HW device test options |
| [ICMP](#icmp) | Administrator | Turn ON/OFF ICMP |
| [ICMPREDIRECT](#icmpredirect) | Administrator | Enable/disable ICMP Redirect |
| [INFO](#info) | Operator | Print Software Capabilities |
| [INITIALIZE](#initialize) | Programmer | Clear file system |
| [INTERNALCNETDebug](#internalcnetdebug) | Operator | Set/View run-time Internal Cresnet debug options. |
| [IPAddress](#ipaddress) | Administrator | Set IP address |
| [IPCONFIG](#ipconfig) | Operator | Display/Configure IP Settings |
| [IPMask](#ipmask) | Administrator | Set IP subnet mask |
| [IPROUTE](#iproute) | Operator | Print Kernel IP routing table |
| [IPTable](#iptable) | Operator | Display IP Table |
| [IPV6](#ipv6) | Administrator | Enable/Disable IPv6 |
| [IPV6AUTOFlowlabels](#ipv6autoflowlabels) | Administrator | Enable/Disable IPv6 auto flow labels |
| [IPV6Address](#ipv6address) | Administrator | Add or remove a static IPv6 address |
| [IPV6Config](#ipv6config) | Administrator | Display current IPv6 settings and information |
| [IPV6DAD](#ipv6dad) | Administrator | Enable/Disable IPv6 duplicate addresss detection |
| [IPV6DESTUnreachable](#ipv6destunreachable) | Administrator | Enable/Disable ICMPv6 destination unreachable messages |
| [IPV6DHcp](#ipv6dhcp) | Administrator | Enable/Disable DHCP for IPv6 |
| [IPV6Defrouter](#ipv6defrouter) | Administrator | Set a static IPv6 default router |
| [IPV6MULTIcast](#ipv6multicast) | Administrator | Enable/Disable multicast proxy for IPv6 |
| [IPV6NDP](#ipv6ndp) | Administrator | IPv6 Neighbor Discovery Protocol information |
| [IPV6PINGResp](#ipv6pingresp) | Administrator | Enable/Disable ping responses for IPv6 |
| [IPV6REDirects](#ipv6redirects) | Administrator | Enable/Disable IPv6 redirects |
| [IPV6ROUTEAdd](#ipv6routeadd) | Administrator | Add a static IPv6 route |
| [IPV6ROUTEDelete](#ipv6routedelete) | Administrator | Delete a static IPv6 route |
| [IPV6ROUTEprint](#ipv6routeprint) | Administrator | Print IPv6 routing table |
| [IPV6SLaac](#ipv6slaac) | Administrator | Enable/Disable SLAAC for IPv6 |
| [ISDIR](#isdir) | Operator | Is the parameter a directory |
| [ISTAT](#istat) | Operator | (*) Check Internal Status of Program |
| [JOINGETINANalog](#joingetinanalog) | Operator | Read Analog Input Joins to Console |
| [JOINGETINDIgital](#joingetindigital) | Operator | Read Digital Input Joins to Console |
| [JOINGETINSErial](#joingetinserial) | Operator | Read Serial Input Joins to Console |
| [JOINGETINTparam](#joingetintparam) | Operator | Read Integer Params to Console |
| [JOINGETOUTANalog](#joingetoutanalog) | Operator | Read Analog Output Joins to Console |
| [JOINGETOUTDIgital](#joingetoutdigital) | Operator | Read Digital Output Joins to Console |
| [JOINGETOUTSErial](#joingetoutserial) | Operator | Read Serial Output Joins to Console |
| [JOINGETSERparam](#joingetserparam) | Operator | Read Serial Params to Console |
| [JOINMONITORSlot](#joinmonitorslot) | Operator | Start/Stop TJI monitor |
| [JOINSETANALOG16](#joinsetanalog16) | Operator | Set Analog Joins from Console for 16 bit Ethernet Id Devices |
| [JOINSETANalog](#joinsetanalog) | Operator | Set Analog Joins from Console |
| [JOINSETDIGITAL16](#joinsetdigital16) | Operator | Set Digital Joins from Console for 16 bit Ethernet Id Devices |
| [JOINSETDIgital](#joinsetdigital) | Operator | Set Digital Joins from Console |
| [JOINSETINTparam](#joinsetintparam) | Operator | Send Integer Parameter from Console |
| [JOINSETPAcket](#joinsetpacket) | Operator | Send Any Packet from Console |
| [JOINSETSERIAL16](#joinsetserial16) | Operator | Send Any Packet from Console for 16 bit Ethernet Id Devices |
| [JOINSETSERParam](#joinsetserparam) | Operator | Send Serial Parameter from Console |
| [JOINSETSErial](#joinsetserial) | Operator | Send Any Packet from Console |
| [JWTALLOWSELFSIGNEdconnection](#jwtallowselfsignedconnection) | Administrator | Whether to use Fusion end point with self-signed certificate |
| [JWTCSPALLOWurlstate](#jwtcspallowurlstate) | Administrator | Whether frame-ancestor directive of CSP allows a page from being loaded from if |
| [JWTPUBLICKEYSOUrce](#jwtpublickeysource) | Administrator | Add Public certificate server url |
| [JWTPUBLICKEYSTAtus](#jwtpublickeystatus) | Administrator | Details of the public key source |
| [KILLSOCKET](#killsocket) | Administrator | Close an active TCP console socket |
| [LIGHTBYPPN](#lightbyppn) | Operator | start squack mode |
| [LIGHTSPAGE](#lightspage) | Operator | (*) show lights panel page |
| [LISTAUTHDOMains](#listauthdomains) | Administrator | List configured authentication domains |
| [LISTBLOCKEDips](#listblockedips) | Administrator | List the blocked IP addresses |
| [LISTDNS](#listdns) | Operator | Display the list of DNS servers |
| [LISTDNSEx](#listdnsex) | Operator | Display the list of DNS servers |
| [LISTDOMAINGroups](#listdomaingroups) | Administrator | List existing domain groups |
| [LISTENSTAT](#listenstat) | Operator | Generate a report of the Ethernet listen sockets |
| [LISTEXTERNALMODules](#listexternalmodules) | Programmer | (*) List information for python modules loaded under this program instance. |
| [LISTGROUPS](#listgroups) | Administrator | List existing local groups |
| [LISTGROUPUsers](#listgroupusers) | Administrator | List all existing (local and domain) users in an existing |
| [LISTLOCKEDUsers](#listlockedusers) | Administrator | List blocked users |
| [LISTPUBKEYFromuser](#listpubkeyfromuser) | Administrator | List existing public key from an existing user account |
| [LISTUSERS](#listusers) | Administrator | List of users authenticated on this system |
| [LOADIPTABle](#loadiptable) | Programmer | Load New IPTable |
| [LOCATION](#location) | Programmer | Location latitude, longitude and city country. |
| [LOGGER](#logger) | Programmer | (*) Turn the logger on, off, or change the operation mode |
| [LOGGERBuffersize](#loggerbuffersize) | Programmer | (*) Set or show the Logger Buffer Size |
| [LOGGERClear](#loggerclear) | Programmer | (*) Clear the Logs for the Specified Program |
| [LOGGERDebuglevel](#loggerdebuglevel) | Programmer | (*) Set or show Logger debug level |
| [LOGGERFlush](#loggerflush) | Programmer | (*) Flush the current buffer to RM |
| [LOGGERMode](#loggermode) | Programmer | (*) View or change the Logger Mode |
| [LOGGERNumbackuplogs](#loggernumbackuplogs) | Programmer | (*) Set or show the Number of Backup Logs desired |
| [LOGGERPrint](#loggerprint) | Programmer | (*) Print the current log to the console |
| [LOGICDebug](#logicdebug) | Operator | (*) Set Logic debug Options |
| [LOGINSTAT](#loginstat) | Administrator | Set time to count valid logins |
| [LOGMESSage](#logmessage) | Programmer | (*) Write a message to the log from the console |
| [LOGOFF](#logoff) | Operator | Logoff current user |
| [MAKEDIR](#makedir) | Programmer | Create a Directory |
| [MDGBSIGnal](#mdgbsignal) | Operator | (*) Set/view Debug flags and signal values |
| [MDNS](#mdns) | Administrator | Change nsswitch mdns configuration |
| [MDNSRETURN](#mdnsreturn) | Administrator | Change nsswitch to return or not return on mdns NOTFOUND |
| [MEMTest](#memtest) | Operator | Memory test |
| [MICDEVICES](#micdevices) | Operator | (*) Microphone Device Info |
| [MIPTable](#miptable) | Programmer | Display Master IP Table |
| [MOVEfile](#movefile) | Programmer | Move a file to a different directory |
| [MYCRESTRON](#mycrestron) | Programmer | Setup MyCrestron Domain & Password, and attempt to register system. |
| [NETWORKSETTINGSRESET](#networksettingsreset) | Operator | Resets networking settings |
| [NEWAPIWEBTOKEN](#newapiwebtoken) | Operator | (*) AVF REST api web token |
| [NUMNOHBRESPonsecnt](#numnohbresponsecnt) | Administrator | Set maximum number of no response allowed for CIP Heartbeat Messaging |
| [NVRAMCLEAR](#nvramclear) | Programmer | Clear NVRAM with zeros |
| [NVRAMGET](#nvramget) | Operator | Retrieve contents of NVRAM from the system |
| [NVRAMPUT](#nvramput) | Programmer | Send contents of NVRAM to the system |
| [NVRAMREBOOT](#nvramreboot) | Operator | Print reboot information |
| [OCSP](#ocsp) | Administrator | Display/Set OCSP configuration for SSL communication. |
| [PACKET](#packet) | Operator | (*) Send custom packets through the RAD tools. |
| [PASSTHRU](#passthru) | Operator | Enter passthru mode console<->device |
| [PASSTO](#passto) | Operator | Enter passto mode console<->device |
| [PAUSEPROGram](#pauseprogram) | Operator | Pauses Specified Program |
| [PING](#ping) | Operator | Ping remote node |
| [PPNDISCOVEr](#ppndiscover) | Operator | Show all PPN devices on cresnet |
| [PRINTAUDITLOG](#printauditlog) | Administrator | Print the audit log. |
| [PROGCOMments](#progcomments) | Operator | (*) Shows program Comments |
| [PROGINFO](#proginfo) | Operator | (*) Show Program Statistics |
| [PROGLOAD](#progload) | Programmer | Loads the specified program |
| [PROGREAdy](#progready) | Operator | Sends the program ready status |
| [PROGREGister](#progregister) | Programmer | Registers/Unregisters the specified program |
| [PROGRESet](#progreset) | Operator | Restarts the specified program |
| [PROGUPTIME](#proguptime) | Operator | (*) Display the time the program is running |
| [PROXY](#proxy) | Administrator | Configure Proxy |
| [PROXYALLOW](#proxyallow) | Administrator | Setup list of hosts that need to use Proxy |
| [RAMFree](#ramfree) | Operator | Show available RAM file space |
| [RCONsole](#rconsole) | Operator | Send Command to Remote console |
| [REBOOT](#reboot) | Operator | Reboot the device |
| [RECOVERYREBOOT](#recoveryreboot) | Operator | Forces system reboot for recovery |
| [REMBLOCKEDip](#remblockedip) | Administrator | Remove an IP Address from the blocked list |
| [REMDns](#remdns) | Administrator | Remove an entry from DNS server List |
| [REMLOCKEDUser](#remlockeduser) | Administrator | Remove user from the blocked list |
| [REMMaster](#remmaster) | Programmer | Remove a master entry to IP table |
| [REMOVEDIR](#removedir) | Programmer | Remove a Directory |
| [REMOVEPUBKEYFromuser](#removepubkeyfromuser) | Administrator | Remove an existing public key from an existing user account |
| [REMOVEUserfromgroup](#removeuserfromgroup) | Administrator | Remove an existing local or domain user from an existing local group |
| [REMPeer](#rempeer) | Programmer | Remove a peer(slave) entry to IP table |
| [REPORTCRESNET](#reportcresnet) | Operator | Show all devices on the main cresnet leg |
| [REPORTPPNTABLe](#reportppntable) | Operator | print PPN table, if any |
| [RESETPHy](#resetphy) | Operator | Reset PHY, may not work on all products. |
| [RESETPassword](#resetpassword) | Administrator | Reset an existing local user's password |
| [RESTORe](#restore) | Administrator | Restore factory defaults |
| [RESUMEPROGram](#resumeprogram) | Operator | Resumes Specified Program |
| [RJSTATUS](#rjstatus) | Programmer | Retrieve RJ requested status |
| [RMLOGerr](#rmlogerr) | Operator | Enable logging errors to the file. |
| [RMTRANSfer](#rmtransfer) | Programmer | Transfer a project to/from removable media |
| [ROUTEADD](#routeadd) | Administrator | Add a static IP route |
| [ROUTEDELete](#routedelete) | Administrator | Delete a static IP route |
| [ROUTEPRINT](#routeprint) | Administrator | Print Kernel IP routing table |
| [ROUTESYMSTAT](#routesymstat) | Operator | (*) Check connection status of route symbols |
| [RPRTCRESNETIDBYPPn](#rprtcresnetidbyppn) | Operator | Report cresnet ID by PPN |
| [RPRTPPNBYCRESNETId](#rprtppnbycresnetid) | Operator | Report PPN by cresnet ID |
| [SDEBUG](#sdebug) | Operator | (*) Check connection status of route symbols |
| [SECURECIPport](#securecipport) | Programmer | Set the secure (SSL) port number for CIP |
| [SECUREGatewaymode](#securegatewaymode) | Administrator | Set/Display secure gateway operation mode. |
| [SECUREWEBSocketport](#securewebsocketport) | Programmer | Set secure Websocket port |
| [SECUREWebport](#securewebport) | Administrator | Set Secure(SSL) port number for Web. |
| [SENDCNETPKT](#sendcnetpkt) | Operator | Send a Cresnet Packet |
| [SENDIPTABLE](#sendiptable) | Programmer | Transfer the IP table to Internal flash |
| [SETCRESNETIDBYPPn](#setcresnetidbyppn) | Operator | Set cresnet ID by PPN |
| [SETCSAUTHENTICATION](#setcsauthentication) | Administrator | Set Control System Authentication credentials. |
| [SETLOCKOUTTIME](#setlockouttime) | Administrator | Set time that an IP is blocked from login |
| [SETLOGINAttempts](#setloginattempts) | Administrator | Set the number of login attempts before blocking IP |
| [SETLogoffidletime](#setlogoffidletime) | Administrator | Set idle time allowed before current user is automatically logged off |
| [SETMULTISLOTANALOGJOIN](#setmultislotanalogjoin) | Programmer | Process a multi slotted analog join |
| [SETMULTISLOTDIGITALJOIN](#setmultislotdigitaljoin) | Programmer | Process a multi slotted digital join |
| [SETMULTISLOTSERIALJOIN](#setmultislotserialjoin) | Programmer | Process a multi slotted serial join |
| [SETPAsswordrule](#setpasswordrule) | Administrator | Set password rules |
| [SETPPNBYCRESNETId](#setppnbycresnetid) | Operator | Set PPN by cresnet ID |
| [SETPPNBYPPn](#setppnbyppn) | Operator | Change old PPN to new PPN |
| [SETSIGnal](#setsignal) | Operator | (*) Set the state of a signal in the program |
| [SETUSERLOCKOUTTime](#setuserlockouttime) | Administrator | Set time that a user is blocked from login |
| [SETUSERLOGINATtempts](#setuserloginattempts) | Administrator | Set the number of login attempts before blocking User |
| [SHOWEXtraerrors](#showextraerrors) | Operator | Enables/disables Show Extra Command |
| [SHOWHW](#showhw) | Operator | Display hardware configuration |
| [SIGDEBUG](#sigdebug) | Administrator | (*) List Sig information for the specified device. |
| [SIGNALTIMESTAMP](#signaltimestamp) | Administrator | (*) Show signal timestamps |
| [SNMP](#snmp) | Administrator | Enable/disable Simple Network Management Protocol |
| [SNMPALLowall](#snmpallowall) | Administrator | Allows All SNMP Managers |
| [SNMPAccess](#snmpaccess) | Administrator | Configure Access Rights for SNMP Communities |
| [SNMPCONTAct](#snmpcontact) | Administrator | Displays Snmp contact information |
| [SNMPLOCATion](#snmplocation) | Administrator | Displays Snmp location information |
| [SNMPMANager](#snmpmanager) | Administrator | Configure an SNMP manager |
| [SNMPMONitor](#snmpmonitor) | Administrator | Configure SNMP Monitoring and trap generation |
| [SNMPTrap](#snmptrap) | Administrator | Send an SNMP trap |
| [SNTP](#sntp) | Administrator | Configure network time synchronization |
| [SOCKETSendtimeout](#socketsendtimeout) | Administrator | Set TCP Socket Send Timeout value in Milliseconds |
| [SPLUSLoad](#splusload) | Operator | (*) Test loading a SIMPL+ module |
| [SPSHOWPOOLERR](#spshowpoolerr) | Operator | (*) Show Smart Thread Pool Error. |
| [SSHARPAPPDEBUGport](#ssharpappdebugport) | Programmer | Enable/Disable and configure S# App Debug SSH port number |
| [SSHARPDebug](#ssharpdebug) | Administrator | (*) Set SimplSharpPro Debugs |
| [SSHPORt](#sshport) | Administrator | Enable/Disable and configure SSH port number |
| [SSHSERVer](#sshserver) | User | Configure the SSH server and the public keys |
| [SSL](#ssl) | Administrator | Display/Set SSL type |
| [SSLVERIFY](#sslverify) | Administrator | Display/Set SSL certificate verification. |
| [SSPTASKs](#ssptasks) | Operator | (*) Show currently executing user threads in SIMPL# Pro. |
| [STOPLIGHTBYPPn](#stoplightbyppn) | Operator | Stop Light And Poll mode |
| [STOPPROGram](#stopprogram) | Operator | Stops the specified program |
| [SUPPORTCIPSHA1Ciph](#supportcipsha1ciph) | Administrator | Enable/Disable use of RSA-SHA1 ciphers. |
| [SUPPORTRSAAES128ciph](#supportrsaaes128ciph) | Administrator | Enable/Disable use of TLS_RSA_WITH_AES_128_CBC_SHA cipher. |
| [SUSERPROGCMD](#suserprogcmd) | Operator | (*) Send a command from the console to the user program |
| [SYMSETSIG](#symsetsig) | Operator | (*) Set the state of the signal in the program |
| [SYSLOG](#syslog) | Operator | Enable/disable system UI log. |
| [SYSMON](#sysmon) | Operator | System Monitor Control |
| [SYSTEMREADY](#systemready) | Programmer | Display the system ready status |
| [TASKSTAT](#taskstat) | Operator | Lists applications in system |
| [TCPKEEPALIVE](#tcpkeepalive) | Programmer | Enable/disable TCP Keep Alive |
| [TEMPTest](#temptest) | Operator | Board Temperature test. |
| [TESTDNS](#testdns) | Operator | Test DNS Server |
| [TESTLOGIn](#testlogin) | Administrator | Test authentication and authorization |
| [TESTLOGOut](#testlogout) | Administrator | Test logout for login via TESTLOGIN |
| [TESTWATCH](#testwatch) | Operator | Test watchdog timer |
| [THREADPOOLINFO](#threadpoolinfo) | Operator | (*) Information about the Custom App Thread pool. |
| [TIMEREVENTMAXQueuesize](#timereventmaxqueuesize) | Administrator | Set queue size to hold maximum timer events |
| [TIMEZone](#timezone) | Administrator | Get/Set the timezone |
| [TIMEdate](#timedate) | Programmer | Get the time and date |
| [TLS13CIPHER](#tls13cipher) | Administrator | Set/Get the class of ciphers/algorithms used for TLS 1.3 encryption |
| [TLSCIPHER](#tlscipher) | Administrator | Set/Get the class of ciphers/algorithms used for TLS 1.2 encryption |
| [TLSVERsion](#tlsversion) | Administrator | Set the minimum TLS version. |
| [TOP](#top) | Operator | Lists proceseses and threads in system |
| [TRACEROUTE](#traceroute) | Administrator | Trace the route of an IP address |
| [TRIGGEREVents](#triggerevents) | Programmer | Trigger timer events for application id. |
| [TYPE](#type) | Operator | Display file contents |
| [UCMD](#ucmd) | Operator | (*) Send a command from the console to the user program |
| [UPDATEPassword](#updatepassword) | User | Update current local user's password |
| [UPGRADERESULTS](#upgraderesults) | Operator | Print results of last upgrade command |
| [UPLOAD](#upload) | Programmer | Load file into cresnet device |
| [UPTIME](#uptime) | Operator | Display the time the system is running |
| [USERInformation](#userinformation) | Administrator | Show access information for a specific user |
| [USERPAGEAUTH](#userpageauth) | Administrator | User page Authentication on/off |
| [USERPAGETokenauth](#userpagetokenauth) | Administrator | User page Token Authentication on/off |
| [USERPROGCMD](#userprogcmd) | Operator | (*) Send a command from the console to the user program |
| [VALIDATEAUTHDOMain](#validateauthdomain) | Administrator | Validate authentication domain configuration |
| [VERsion](#version) | Operator | Print version to console |
| [WAVEDUMP](#wavedump) | Operator | (*) Dump Logic Wave Information |
| [WBALLOW](#wballow) | Operator | (*) wballow |
| [WBBTN](#wbbtn) | Operator | (*) wbbtn |
| [WBDELETEPAIRING](#wbdeletepairing) | Operator | (*) wbdeletepairing |
| [WBINIT](#wbinit) | Operator | (*) wpinitt |
| [WBIP](#wbip) | Operator | (*) wpip |
| [WBJOIN](#wbjoin) | Operator | (*) wbjoin |
| [WBLEAVE](#wbleave) | Operator | (*) wbleave |
| [WBPAIR](#wbpair) | Operator | (*) wppair |
| [WBSHOW](#wbshow) | Operator | (*) wpshow |
| [WBSTART](#wbstart) | Operator | (*) wbstart |
| [WBSTOP](#wbstop) | Operator | (*) wbstop |
| [WBSTOPWITHSNAPSHOT](#wbstopwithsnapshot) | Operator | (*) wbstopwithsnapshot |
| [WBSTOPWITHTIMELINE](#wbstopwithtimeline) | Operator | (*) wbstopwithtimeline |
| [WBUNPAIR](#wbunpair) | Operator | (*) wpunpair |
| [WEBINIT](#webinit) | Programmer | Initialize Webserver default file. |
| [WEBPORT](#webport) | Administrator | Set port number for Webserver. |
| [WEBSERVER](#webserver) | Administrator | Enable/disable Webserver |
| [WEBSOCKETTOKEN](#websockettoken) | Administrator | Manage JWT authorization token |
| [WHO](#who) | Administrator | Generate a report of the Ethernet consoles |
| [WHOAmi](#whoami) | Operator | Display current user's identity |
| [XGETfile](#xgetfile) | Operator | Use XMODEM to transfer file from ROM |
| [XPUTfile](#xputfile) | Operator | Use XMODEM to transfer file to ROM |

---

## Command Details

### 3STONES

**Role:** Administrator | **Description:** Test watchdog timer

```
3STONES
No parameters
```

### 8021XAUthenticate

**Role:** Administrator | **Description:** Enable/Disable 802.1x Authentication.

```
8021xAuthenticate [ON |OFF]
	ON           - Enable 802.1x Supplicant Authentication
	OFF          - Disable 802.1x Supplicant Authentication
	No parameter - displays current setting
```

### 8021XDOMain

**Role:** Administrator | **Description:** Configure/View 802.1x Domain Name.

```
8021xDomainName [Domain Name]
	DomainName   - Update Domain Name To Domain Specified
	No parameter - displays current setting
```

### 8021XMEThod

**Role:** Administrator | **Description:** Configure/View EAP Method.

```
8021xMethod [Password |Certificate |List]
	Password     - 802.1x Suplicant Will Use Secured Password (EAP MSCHAP V2) EAP Method
	Certificate  - 802.1x Suplicant Will Use Certificate EAP Method
	List         - 802.1x Suplicant Will display the supported EAP Methods
	No parameter - displays current setting
```

### 8021XPASsword

**Role:** Administrator | **Description:** Configure 802.1x Password.

```
8021xPassword [Password]
	{Password}      - Update Password To One Specified 
	No parameter    - Echo back command
```

### 8021XSENdpeapver

**Role:** Administrator | **Description:** Enable/Disable 802.1x Peap version reporting.

```
8021xSendPeapVer [ON |OFF]
	ON           - enable 802.1x peap version number report 
	OFF          - disable 802.1x peap version number report 
	No parameter - displays current setting
	Note: This setting only applies for 8021xMethod Password
	Does not work with Windows 2012 radius server
```

### 8021XTRUStedcas

**Role:** Administrator | **Description:** Select/List 802.1x Trusted CA Certificates

```
8021xTrustedCAs [LIST|USE|DONTUSE] [<Certificate #>|Name UID])
	LIST                 - List All Trusted Certificates
	LISTN                - List and number all Trusted Certificates
	LISTU                - List only Trusted Certificates marked use
	USE [#|Name UID]     - Add Specified Certificate To List Of Certificates Used To Validate The Server
	DONTUSE [#|Name UID] - Remove Specified Certificate From List Of Certificates Used To Validate The Server
	No parameter - Display this help message
```

### 8021XUSERname

**Role:** Administrator | **Description:** Configure/View 802.1x User Name.

```
8021xUsername Password <Name> 
	Password        - Displays current settings
	Password {Name} - Update User Name To Name Specified 
	No parameter    - Displays current settings
```

### 8021XVALidateserver

**Role:** Administrator | **Description:** Require Validation Of 802.1x Authentication Server's Certificate.

```
8021xValidateServer [OFF|ON]
	OFF - 802.1x supplicant will not validate authentication server's certificate
	ON - 802.1x supplicant will validate authentication server's certificate
	No parameter - displays current setting
```

### ADDAUTHDOMain

**Role:** Administrator | **Description:** Add authentication domain details

```
ADDAUTHDOMAIN -N:domain_name -H:host -D:device_account
   [{-K:keytab_file | -A:admin_account [-P:admin_password]}] [-T:AD] [-R:realm_name] [-V]
ADDAUTHDOMAIN -N:domain_name -H:host -T:RADIUS [-P:shared_secret] [-V]
where:
   -N:domain_name - specifies the name of the authentication domain to configure
   -H:host - specifies either an IP address (v4 or v6) or server name that will
      authenticate/authorize users logging in to this device
   -T:domain_type - indicates the authentication/authorization protocol to use
      for network logins with this domain (defaults to AD if not provided)
   -V - attempts to validate the configuration with the domain
   for RADIUS domains:
     -P:shared_secret - the password to authenticate this device to a domain-side server
   for AD domains:
     -D:device_account - the domain-side computer account associated with this device
     -K:keytab_filename - name of the keytab file to use when joining the domain manually
        The keytab file must be uploaded to the SYS folder on the device, and will use a
        default name if neither keytab file nor admin credentials are specified
     -A:admin_account - domain administrator account to use when joining the domain automatically
     -P:admin_password - password for the admin_account
     -R:realm_name - name of the authentication realm
        (defaults to '<DOMAIN_NAME>' if not specified)
```

### ADDBLOCKEDip

**Role:** Administrator | **Description:** Add an IP Address to the blocked list

```
ADDBLOCKEDip [ipaddress]
	ipaddress - ip address to block
	No parameter - display current list of blocked ip addresses
```

### ADDDOMAINGroup

**Role:** Administrator | **Description:** Create a new domain group

```
ADDDOMAINGROUP -N:domaingroupname -L:accesslevel 

	-N: specifies the domain group name 
	-L: specifies one of the following access level:
		A - as an Administrator
		P - as a Programmer
		O - as an Operator
		U - as a User
		C - for Connection only
```

### ADDDns

**Role:** Administrator | **Description:** Add an entry to DNS server List

```
ADDDns ip_address
	ip_address - IP address in dot decimal notation
```

### ADDGroup

**Role:** Administrator | **Description:** Create a new local group

```
ADDGROUP -N:groupname -L:accesslevel 

	-N: specifies the group name 
	-L: specifies one of the following access level:
		A - as an Administrator
		P - as a Programmer
		O - as an Operator
		U - as a User
		C - for Connection only
```

### ADDHOSTS

**Role:** Administrator | **Description:** Add hosts entries

```
ADDHOSTS host.com=1.1.1.1;host2.edu=2.2.2.2
	Issue "ADDHOSTS -c" to clear list
```

### ADDLOCKEDUser

**Role:** Administrator | **Description:** Add user to the blocked list

```
ADDLOCKEDuser [username]
	username - user to block
	No parameter - display current list of blocked users
```

### ADDMaster

**Role:** Programmer | **Description:** Add a master entry to IP table

```
Format: ADDMaster cip_id ip_address/name 
	cip_id - ID of the CIP node (in hex)
	ip_address/name - IP address (IPv4 or IPv6) 
	                - or name of the site for DNS lookup
```

### ADDPUBKEYTouser

**Role:** Administrator | **Description:** Add a public key to an existing user account

```
ADDPUBKEYtouser -N:username -K:keyfilename
	-N: specifies name of a local user
	-K: specifies name of a public key file pre-uploaded to \user folder
```

### ADDPeer

**Role:** Programmer | **Description:** Add a peer(slave) entry to IP table

```
Format: ADDPeer cip_id ip_address/name [-D:device_id] [-C:cipport] [-P:program] [-U:RoomId]
	cip_id - ID of the CIP node (in hex)
	ip_address/name - IP address (IPv4 or IPv6) 
	                - or name of the site for DNS lookup
	RoomId  - Upto 32 characters. Valid characters are A-Z and 0-9.
	               -	This is used for communication with a Virtual Control server
	device_id       - ID in device redirection table (in hex) (must be < 256)
	port number     - port number for the connection (in dec) (must be > 256)
	program         - program number which uses device (in dec) (default 1)
```

### ADDUSER

**Role:** Administrator | **Description:** Create a new local user

```
ADDUSER -N:username {-P:password}
	-N: specifies name of the local user to be created
	-P: specifies the password for the user
```

### ADDUSERTogroup

**Role:** Administrator | **Description:** Add an existing local or domain user to an existing local group

```
ADDUSERTOGROUP -N:username -G:groupname 
	-N: specifies name of a local user or domain (domain\user) user
	-G: specifies name of a local group
```

### ADLOGIN

**Role:** Administrator | **Description:** Active Directory Login

```
ERROR: ADLOGIN disabled when configured authentication domains are in use
```

### ADLOGOUt

**Role:** Administrator | **Description:** Active Directory Logout

```
ERROR: ADLOGOUT disabled when configured authentication domains are in use
```

### APIWEBTOKEN

**Role:** Operator | **Description:** (*) AVF REST api web token

*No detailed help available.*

### APPSTATs

**Role:** Operator | **Description:** Dumps out Registered App Stats

```
APPSTATS {-P:ALL | -P:Specific Program Identifier}
 	 -P:  Dump app info for a specific program.   If not present, ALL assumed.
```

### AUCANCEL

**Role:** Administrator | **Description:** Cancel the auto update in progress.

```
AUCANCEL
	 No Parameters - Cancels any pending auto update.
```

### AUCHECKNOW

**Role:** Administrator | **Description:** Check for updates now.

```
AUCHECKNOW
	 No Parameters - Checks for auto update actions now.
```

### AUDEVCONNECTPASS

**Role:** Administrator | **Description:** Get/Set the password used by auto update to login to Crestron devices.

```
AUDEVCONNECTPASS [password]
	 password - Password for connecting to remote devices.
	          - To clear password use keyword "none" as password.
	 No Parameters - Displays current setting
```

### AUDEVCONNECTUSER

**Role:** Administrator | **Description:** Get/Set the username used by auto update to login to Crestron devices.

```
AUDEVCONNECTUSER [username]
	 username - Username for connecting to remote devices.
	          - To clear username use keyword "none" as username.
	 No Parameters - Displays current setting
```

### AUDISALLOWDOWNGRADE

**Role:** Administrator | **Description:** If ON will not allow Firmware downgrade else allow firmware downgrade.

```
AUDISALLOWDOWNGRADE [ON | OFF]
	 [ON] Firmware downgrade is NOT allowed.
	 [OFF] PUF downgrade is allowed.
	 No Parameters - Displays current setting.
```

### AUDITLogging

**Role:** Administrator | **Description:** Display or Change the current audit logging operation.

```
AUDITLogging [ON|OFF|CLEAR|PRINT|PRINTALL] {[ALL]|[NONE]|{[ADMIN] [PROG] [OPER] [USER]} [REMOTESYSLOG]}
	ON - Enable Logging
	OFF - Disable Logging
	CLEAR - Clears audit log (alias for CLEARAUDITLOG)
	PRINT - Print last 50 lines of audit log (alias for PRINTAUDITLOG)
	PRINTALL - Print entire audit log (alias for PRINTAUDITLOG ALL)
	No parameter - Displays current setting
NOTE: Logons, logoffs, & account management is always logged
- optional, used to log commands by access level
	ADMIN - Administrator
	PROG - Programmer
	OPER - Operator
	USER - User
	ALL - All Access Levels
	NONE - No Command Logging
Example: 'AUDITLOGGING ON ADMIN OPER'
	REMOTESYSLOG - Write to the remote syslog server only.
```

### AUENABLE

**Role:** Administrator | **Description:** Enable/disable automatic updates.

```
AUENABLE [ON|OFF]
	 Enable/disable auto updates.
	 No Parameters - Displays current setting
```

### AUFORCEUPDATENOW

**Role:** Administrator | **Description:** Force updates now.

```
AUFORCEUPDATENOW
	 No Parameters - Forces manifest file to be processed now.
```

### AUMANIFESTURL

**Role:** Administrator | **Description:** Get or Set auto updater manifest URL.

```
AUMANIFESTURL [URL]
	URL - URL of Manifest file.
	NONE- clear the of Manifest url path.
	No Parameters - Displays current setting
```

### AUPASSWORD

**Role:** Administrator | **Description:** Get/Set the password used by auto update to login to the update server.

```
AUPASSWORD [password]
	 password - Password for downloading auto update files.
	          - To clear password use keyword "none" as password.
	 No Parameters - Displays current setting
```

### AUPEERVERIFY

**Role:** Administrator | **Description:** If ON perform peer verification else no peer verification.

```
AUPEERVERIFY [ON | OFF]
	 [ON] PEER verification will be peformed.
	 [OFF] PEER verification will NOT be peformed.
	 No Parameters - Displays current setting.
```

### AUPLUGINCATALOGURL

**Role:** Administrator | **Description:** Get or Set auto updater plugin catalog URL.

```
AUPLUGINCATALOGURL [URL]
	URL - URL of Plugin Catalog file.
	NONE- To go back to the Default Plugin Catalog URL which is https://www.crestron.com/autofwupdates/AU-Plugin-Catalog.txt.
	No Parameters - Displays current setting
```

### AUPOLLINTERVAL

**Role:** Administrator | **Description:** Set how long to wait before checking for updates again.

```
AUPOLLINTERVAL [interval_in_minutes]
	 interval_in_minutes - How many minutes to wait before checking for updates.
	                       Will be rounded up to the nearest hour.  0 to disable.
	 No Parameters - Displays current setting
```

### AUSTATUS

**Role:** Programmer | **Description:** Reports the auto update status.

```
AUSTATUS
	 No Parameters - Displays current auto update status
```

### AUTHDOMAINMode

**Role:** Administrator | **Description:** Display or change authentication domain mode

```
AUTHDOMAINMode [ON|OFF]
	'ON' enables authentication domain mode and disables legacy AD login
	'OFF' disables authentication domain mode and enables legacy AD login
	No parameter - displays current setting
```

### AUTHentication

**Role:** Administrator | **Description:** Authentication on/off

```
AUTHENTICATION [OFF | ON]
	ON - turns on authentication.
	OFF - is disabled. User cannot turn OFF Authentication.
	No parameter - displays current setting
```

### AUTIME

**Role:** Administrator | **Description:** Set a scheduled time for when to check for updates.

```
AUTIME [TIME]
	 TIME is [SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY] HH:MM
	    HH:MM:  24 hour time when the manifest file should be read.
	    Specifying only HH:MM will make the update run every day at that time.
	    Specifying the day in addition HH:MM will make the update run only at that day and time each week.
	 To clear time use keyword "none" as [TIME].
	 No Parameters - Displays current setting
```

### AUTOBRIGHTNESS

**Role:** Programmer | **Description:** Configure auto-brightness.

```
AUTOBRIGHTNESS [LCDON | LCDOFF | LCDHI | LCDLO | FBON | FBOFF]
	LCDON           Enable LCD auto-brightness
	LCDOFF          Disable LCD auto-brightness
	LCDHI [level]   brightness level (0 - 100)
	LCDLO [level]   brightness level (0 - 100)
	LCDTHRESH [level]   Threshold level (0 - 100)
	FBON       Enable  ALS feedback
	FBOFF      Disable ALS feedback
	No Parameters   Displays current setting
```

### AUTODIScovery

**Role:** Operator | **Description:** Commands for Ethernet auto discovery

```
AUTODISCOVERY [ON | OFF | QUERY | LIST | HOSTS | SETNUMTIMESQUERYMSGSENT times | SETDELAYBETWEENQUERYMSGINMS delayInMs | OPTION autodiscoveryqueryoption | ADAPTER autodiscoveryadapteroption]
	on : enables autodiscovery functions
	off : disables autodiscovery functions
	query : runs the discovery query
	list : displays the list of nodes discovered
	hosts : displays the list of hostnames
		NoForceAll : Will not force all the devices into light-n-poll mode if the specified device type is not found.
	setnumtimesquerymsgsent : Set the number of times the query message is sent.
	setdelaybetweenquerymsginms : Set the delay (in msec) between sending each query message.
	option : Sets autodiscovery query message option [HOSTNAME | IPADDRESS | HOSTNAME_IPA].
	adapter : Sets autodiscovery adapter option [LAN | CS | BOTH].
```

### AUTODIScovery

**Role:** Operator | **Description:** Commands for Ethernet auto discovery

```
AUTODISCOVERY [ON | OFF | QUERY | LIST | HOSTS | SETNUMTIMESQUERYMSGSENT times | SETDELAYBETWEENQUERYMSGINMS delayInMs | OPTION autodiscoveryqueryoption | ADAPTER autodiscoveryadapteroption]
	on : enables autodiscovery functions
	off : disables autodiscovery functions
	query : runs the discovery query
	list : displays the list of nodes discovered
	hosts : displays the list of hostnames
		NoForceAll : Will not force all the devices into light-n-poll mode if the specified device type is not found.
	setnumtimesquerymsgsent : Set the number of times the query message is sent.
	setdelaybetweenquerymsginms : Set the delay (in msec) between sending each query message.
	option : Sets autodiscovery query message option [HOSTNAME | IPADDRESS | HOSTNAME_IPA].
	adapter : Sets autodiscovery adapter option [LAN | CS | BOTH].
```

### AUTONegotiate

**Role:** Administrator | **Description:** Set Ethernet Auto Negotiation

```
AUTONEGOT [device_num] (ON | 10HALF | 10FULL | 100HALF | 100FULL)
	device_num - optional number of device to set (0)
	ON - autonegotiation is ON
	10HALF - autonegotiation is OFF, use 10mps, half duplex.
	10FULL - autonegotiation is OFF, use 10mps, full duplex.
	100HALF - autonegotiation is OFF, use 100mps, half duplex.
	100FULL - autonegotiation is OFF, use 100mps, full duplex.
	No parameter - displays current setting
```

### AUUSERNAME

**Role:** Administrator | **Description:** Get/Set the username used by auto update to login to the update server.

```
AUUSERNAME [username]
	 username - Username for downloading auto update files.
	          - To clear username use keyword "none" as username.
	 No Parameters - Displays current setting
```

### AUVERIFYSIGNATURE

**Role:** Administrator | **Description:** If ON perform firmware signature verification else no signature verification.

```
AUVERIFYSIGNATURE [ON | OFF]
	 [ON] Firmware Signature verification will be peformed.
	 [OFF] Firmware Signature verification will NOT be peformed.
	 No Parameters - Displays current setting.
```

### AVFRESTORE

**Role:** Operator | **Description:** (*) Set the AVF configuration for Factory default

*No detailed help available.*

### AVFTIMER

**Role:** Programmer | **Description:** (*) avtimer [start|stop]

*No detailed help available.*

### AVFVER

**Role:** Operator | **Description:** (*) Displays AV Framework version

*No detailed help available.*

### BACNETAUTODiscovery

**Role:** Administrator | **Description:** Disables/enables Auto Discovery for remote devices/objects

```
BACnet stack is not running. Command unavailable..
```

### BACNETBDT

**Role:** Operator | **Description:** Writes or reads a BACnet Broadcast Distribution Table (BDT)

```
ERROR: BACnet stack is not running. Command unavailable..
```

### BACNETDETECTOffline

**Role:** Operator | **Description:** Enables/disables remote device offline detection

```
BACnetDetectOffline [0/1] 
Enable[0]/Disable[1] the online detection for the remote devices
```

### BACNETDEVICediscovery

**Role:** Administrator | **Description:** Starts/stops device discovery

```
BACnet stack is not running. Command unavailable..
```

### BACNETDEVicescantime

**Role:** Administrator | **Description:** Sets remote device discovery time

```
BacnetDeviceScanTime 
	Remote device discovery time
	Parameter -[TIME in Minutes] 
	[Range 1-1440, 0 Discovery Disable]
```

### BACNETDISPLAYdiscovery

**Role:** Administrator | **Description:** Displays discovery data

```
BACnet stack is not running. Command unavailable..
```

### BACNETDIsablereadfwrite

**Role:** Administrator | **Description:** Disables/enables the read request followed by write

```
BacnetDisableReadFWrite [1/0] 
Disable/Enable the Read Request Followed by Write Request.
```

### BACNETENBBMDACCEPtfd

**Role:** Administrator | **Description:** Enables/disables BBMD Accept FD Registrations functionality

```
BACnet stack is not running. Command unavailable..
```

### BACNETEnablebbmd

**Role:** Administrator | **Description:** Enables/disables BBMD functionality

```
BACnet stack is not running. Command unavailable..
```

### BACNETGETCUrrentload

**Role:** Administrator | **Description:** Displays the stack internal resources usage

```
BacnetGetCurrentLoad
	  Displays the stack internal resources usage
```

### BACNETGETMEMusage

**Role:** Operator | **Description:** Gets current and peak memory usage for BACnet Stack...

```
BACNETGETMEMusage
	No Parameter - Displays BACnet Stack Heap Memory Usage
```

### BACNETGEtobjectcount

**Role:** Operator | **Description:** Displays BACnet object count

```
BACNETGetObjectcount
	No Parameter - Display Number of BACnet devices and objects present.
	No Parameter - This is the count of devices and objects which are available for use.
```

### BACNETHOSTCovsupport

**Role:** Administrator | **Description:** Enables/disables COV support for the Host objects

```
BacnetHostCOVSupport [1/0] 
Enable[1]/Disable[0] the COV support for Host device
```

### BACNETHostcovlist

**Role:** Operator | **Description:** Displays list of COV subscriptions with the Host device

```
DisplayHostCOVList [RemoteAddress]

 	Displays all the hosted objects that a remote device has subscribed for COV notifications.
	[RemoteAddress] Displays number of subscribed COV entries for the host object specified by RemoteAddress
```

### BACNETLIstobjectprop

**Role:** Operator | **Description:** Lists BACnet device/object properties.

```
BACnetListObjectProp <DevID> <ObjectType> <ObjectID>
	<DevID> - Device Identifier 
	<ObjectType> - Object Type 
	<ObjectID> - Object Identifier 
	Display BACnet object property..
```

### BACNETMAXapdutimeout

**Role:** Administrator | **Description:** Sets maximum APDU Timeout for request retry

```
BacnetMaxAPDUTimeOut [1000/10000]ms 
Set the maximum response timeout for next retry
```

### BACNETNUmberofretries

**Role:** Administrator | **Description:** Sets the maximum number of retries

```
BacnetNumberOfRetries [0/3] 
Set the maximum number of BACnet request retries
```

### BACNETOBJECtdiscovery

**Role:** Administrator | **Description:** Starts/stops object discovery of a remote device

```
BACnet stack is not running. Command unavailable..
```

### BACNETObjectlist

**Role:** Operator | **Description:** Lists all BACnet objects configured

```
ListObject [Device ID] [Object Type]
	Displays Number of BACnet objects configured
	If [Device ID] Specified, Displays Number BACnet Objects Specified by Device ID
	If [Device ID] [Object Type] Specified, Displays BACnet Objects Of Device ID With Specified Object Type

Total Count : 0
```

### BACNETPRIorityforhostwp

**Role:** Administrator | **Description:** Sets the write priority for the hosted objects

```
BacnetPriorityForHostWP 
Set the write priority for the hosted objects 
 Enter between 1 to 16. [1 - High priority, 16 - Low Priority]
```

### BACNETREMOTECOVType

**Role:** Administrator | **Description:** Sets COV type ((Un)Confirmed) for the remote objects

```
BACnetRemoteCOVType [1/0] 
Confirmed[1]/UnConfirmed[0] COV support for remote objects
```

### BACNETREMOTEstatuslist

**Role:** Operator | **Description:** Displays remote devices online/offline status

```
BacnetRemoteStatusList
	 Display remote devices online/offline status.
```

### BACNETREMotecovlist

**Role:** Operator | **Description:** Displays list of Host COV subscriptions with the Remote device

```
DisplayRemoteCOVList
	  Displays all the remote objects that the program has subscribed to COV for.
```

### BACNETRegasfd

**Role:** Administrator | **Description:** Registers Control System As Foreign Device

```
BACnetRegAsFD [P] [IP Address/Hostname] [Port Number (in Hex)] [Time To Live (in seconds)]
	BACnetRegAsFD [M/U/R]
	Changes(M) device mode to Foreign, Registers(R) Or Disable(U) Device As BACnet Foreign Device
```

### BACNETSETBIndlimit

**Role:** Administrator | **Description:** Sets the maximum remote device binding with the host device

```
BacnetSetRemoteBindLimit [1/65535] 
Set the maximum number of remote device binding with the host device
```

### BACNETSETDLYBTnwhoisreq

**Role:** Administrator | **Description:** Sets delay between WhoIs request groups

```
BacnetDelayBetweenWhoIsRequests [Group size] [Delay in milliseconds] 
	Set delay between group of Who-Is requests
	Parameter -[Group size] 
	[Size range: 1-100]
	Parameter -[Delay in milliseconds] 
	[Minimum is 0 ms, maximum 10000 ms]
```

### BACNETSETNEtworknum

**Role:** Administrator | **Description:** Sets the Network Number

```
BacnetSetNetworkNum [0-65534] 
Set the Network Number for host device
```

### BENCHMARKS

**Role:** Administrator | **Description:** Run Platform benchmarks

```
BENCHMARKS {Test Number}
1 - Run All Benchmarks
2 - Platform Time Reference
3 - Benckmark Threads
4 - Benchmark Mutex
5 - Benchmark CriticalSection
6 - Benchmark Crestron Queue
```

### BLUETOOTH

**Role:** Programmer | **Description:** Configure bluetooth feature

```
Get or Set some parameter
BLUETOOTH [NAME] [value]
	NAME  - set the device name (max 8)
```

### BROADcast

**Role:** Operator | **Description:** Enable Error Broadcast

```
BROADCAST [ON | OFF]
	No parameter - displays current setting
```

### BTPAN

**Role:** Programmer | **Description:** Configure bluetooth PAN feature

```
BTPAN [ENABLE | DISABLE] 
 	 Enable - enables bluetooth PAN profile.
 	 Disable - disables bluetooth PAN profile.
```

### BYE

**Role:** Operator | **Description:** Close user session

*No detailed help available.*

### CAMDEVICES

**Role:** Operator | **Description:** (*) Camera Device Info

*No detailed help available.*

### CARDS

**Role:** Operator | **Description:** Display Cards Detected in System

```
CARDS 
 No parameters
```

### CCDCLOUDREPORTER

**Role:** Programmer | **Description:** (*) Tests cloud registration

*No detailed help available.*

### CCDINFO

**Role:** Programmer | **Description:** (*) Prints out information regarding all the loaded drivers

*No detailed help available.*

### CCDLOGGING

**Role:** Programmer | **Description:** (*) Toggles general logging for the driver

*No detailed help available.*

### CCDLOGGINGLEVEL

**Role:** Programmer | **Description:** (*) Sets the logging level for the driver

*No detailed help available.*

### CCDRXDEBUG

**Role:** Programmer | **Description:** (*) Toggles connection transport (RX) logging

*No detailed help available.*

### CCDSTACKTRACE

**Role:** Programmer | **Description:** (*) Toggles stack trace printing when exceptions occur

*No detailed help available.*

### CCDSTATES

**Role:** Programmer | **Description:** (*) Prints out driver states

*No detailed help available.*

### CCDTXDEBUG

**Role:** Programmer | **Description:** (*) Toggles connection transport (TX) logging

*No detailed help available.*

### CD

**Role:** Operator | **Description:** Change directory

```
CD [directory] 
	directory - string containing directory specification
	No parameter - display current setting
```

### CERTIFicate

**Role:** Administrator | **Description:** Add, Remove, List or View Certificates

```
CERTIFicate Cmd Certificate_Store <Certificate_Name> <Certificate_UID> <Password>
	Where Cmd = [ADD|REM|LIST|LISTN|VIEW]
	Where Certificate_Store = [ROOT|MACHINE|INTERMEDIATE|SIP|STREAM|WEBSERVER|WEBSOCKET]
	ADD  Certificate_Store - Add Certificate(from known location) To Specified Certificate Store
		(MACHINE,SIP,STREAM,WEBSERVER,WEBSOCKET stores requires password)
	ADDF filename Certificate_Store - Add Certificate To Specified Certificate Store
	REM  Certificate_Store [#|Certificate_Name Certificate_UID] - Remove Specified Certificate From Specified Certificate Store
	LIST Certificate_Store - List All Certificates In Specified Certificate Store
	LISTN Certificate_Store - List and number all Certificates In Specified Certificate Store
	VIEW Certificate_Store [#|Certificate_Name Certificate_UID] - View Details Of Specified Certificate In Specified Certificate Store

CERTIFicate SELFEXPIREREBOOT [ENABLE|DISABLE]
	ENABLE - enables device auto-reboot when the self-signed certificate expires (default)
	DISABLE - disables device auto-reboot when the self-signed certificate expires

CERTIFicate SELFEXPIREREBOOTTIME [HH:MM]
	Specifies the time when the device will reboot following regeneration of the self-signed certificate
	Where HH:MM = Hours between 0-23 and Minutes between 0-59

	No parameter - Lists Usage
```

### CIPPORT

**Role:** Programmer | **Description:** Set port number for CIP

```
CIPPORT [portnumber]
	portnumber - desired port number > 4096 (in decimal).
	No parameter - displays current value
```

### CIPTIMESET

**Role:** Administrator | **Description:** Enable/Disable setting of time via CIP

```
CIPTIMESET [allow/ignore]
	allow	Device will accept time set packets via CIP
	ignore	Device will ignore time set packets via CIP
```

### CLEARAUDITLOG

**Role:** Administrator | **Description:** Clear the audit log.

```
CLEARAUDITLOG
	No parameter - Clears the audit log
```

### CLEARCAMERAS

**Role:** Operator | **Description:** (*) Camera Device Info

*No detailed help available.*

### CLEARCSAUTHENTICATION

**Role:** Administrator | **Description:** Clear Control System Authentication credentials.

```
ClearCSAuthentication 
Clear Control System Authentication parameters for CIP connect message.
```

### CLEAREVents

**Role:** Administrator | **Description:** Clear application timer events

```
Clear all timer events for specified event group within application program id. 
CLEAREVENTS -I:ProgramTag -G:GroupEventName 
	 -I: ProgramTag/UserDefinedTag 
	 -G: Group Event Name
```

### CLEAREXTERNALMODules

**Role:** Programmer | **Description:** Clears the persistent data of external modules.

```
CLEAREXTERNALMODules -P:ALL | -P:Specific Program Identifier
	 -P: The App ID of the program or ALL
```

### CLEARLIGHTS

**Role:** Operator | **Description:** (*) Clear Light Configs

*No detailed help available.*

### CLEARerr

**Role:** Operator | **Description:** Clears the current error log

```
CLEARERR
	Clears the current error log.
```

### CLOUDPROXYAUTH

**Role:** Administrator | **Description:** Sets the authentication method for connecting to a proxy

```
Sets the specified authentication methods to try when connecting to a proxy, the methods must be space delimited
CLOUDPROXYAUTH: [None | Basic | Digest | Digest_IE | NTLM | ANY | ANYSAFE | ONLY]
	None - no authentication
	Basic - Most commonly used and supported, username/password are sent in clear text (DEFAULT)
	Digest - More secure than BASIC, username/password are NOT sent in clear text
	Digest_IE - Digest authentication with an IE flavor
	NTLM - A proprietary protocol invented and used by Microsoft. It uses a challenge-response and hash concept similar to Digest, to prevent the password from being eavesdropped
	ANY - Automatically selects whatever is suitable, the most secure option is preferred
	ANYSAFE - Automatically selects whatever is suitable except 'BASIC', the most secure option is preferred
	ONLY - Specifies that if authentication is required only the seleced method is acceptable
```

### CLOUDPROXYURL

**Role:** Administrator | **Description:** Sets the url of the proxy used to make requests

```
Sets the url of the proxy used to make requests
CloudProxyUrl: [scheme://][username:password@][hostname | ipAddress][:port]
	scheme - The scheme of the request: http, socks4, socks5, etc. If no scheme entered, defaults to http
	username - The username used to connect to the proxy server (OPTIONAL)
	password - The password used to connect to the proxy server (OPTIONAL)
	hostname - The hostname of the proxy server
	ipAddress - The ip address of the proxy server
	port - The port number the proxy server is listening on (OPTIONAL, default '1080')
Use 'clear' to clear the current url
```

### CONFIGUTILS

**Role:** Administrator | **Description:** Configuration utilities for data export and import

```
CONFIGUTILS [EXPORTALL|IMPORTALL] [-P[:password]] [-D:directory]
	 Warning: IMPORTALL will do a reboot.
	 EXPORTALL:        export ALL data setting to firmware folder
	 IMPORTALL:        import ALL data setting from firmware folder
	 -F                Don't prompt for import
	 -P[:password]     encrypt data with password.  If password is not given, it will be prompted for
	 -D:directory      Alternative directory to store backup
```

### CONSOLESETMICGAIN2

**Role:** Operator | **Description:** (*) MicId, gainValue

*No detailed help available.*

### COPYfile

**Role:** Programmer | **Description:** Copy a file to a different directory

```
COPYfile sourcespec destspec 
	sourcespec - source file name specification (could be relative to current dir)
	destspec - destination file name specification (could be relative to current dir)
	filenames with embedded spaces must be enclosed in double quotes("The File")
```

### CORE3XPANELWEB

**Role:** Programmer | **Description:** Configure the core3 XPanel Flash policy server

```
Core3XpanelWeb [ON | OFF] [DOMAIN] [PORT(s)] [SECURE_OFF | SECURE_ON]
	ON - enables Smart Graphics XPanel Web
	OFF - disables Smart Graphics XPanel Web
	DOMAIN - sets Smart Graphics XPanel Web domain
	PORT(s) - sets Smart Graphics XPanel Web port(s) (0 to use default port, * to open all ports. Other valid input examples: "64232" or "64232,6700-8900")
	SECURE_OFF - Smart Graphics XPanel Web can only connect to control system using an unencrypted connection
	SECURE_ON - Smart Graphics XPanel Web can only connect to control system using encrypted TLS/SSL. Note: SSL must be ON and CA Signed
	No parameter - displays current setting.
```

### COREDUMPSLEEPtime

**Role:** Operator | **Description:** Display watchdog coredump sleep time (in seconds)

```
COREDUMPSLEEPTIME [timeout] in seconds (Range 30 to 180 seconds)
No parameter - displays current timeout setting
```

### CREATECsr

**Role:** Administrator | **Description:** Generate a CSR.

```
CREATECSR C:ST:L:O:OU:CN:E [-I:<option>] [-S:<altname>[,<altname>],...]
	where C = 2 letter country code
	where ST = Full state or province name
	where L = Locality or city name
	where O = Organization or company name
	where OU= Organizational Unit name or division
	where CN = site name or domain name
	where E = Email address
	where -I: Ignore blank parameters
	  <option> is 'true' or 'false'
	where -S: Subject Alternative Name parameter(s)
	  <altname> is a type:value; the only valid type is 'DNS'
	Values that contain spaces must be enclosed in quotes.
```

### CSIODebug

**Role:** Operator | **Description:** Set/View run-time CSIO debug options.

```
CSIODEBUG
View incoming and outgoing packets on the CSIO interface
[ON/OFF] Turns on and off debug trace.
	 No Parameters - Displays current debug settings
```

### CSONLINEUPTIME

**Role:** Programmer | **Description:** Get CS online uptime

```
CSONLINEUPTIME 
	 no Parameters needed
```

### CSPROJECTRemove

**Role:** Programmer | **Description:** Remove the project from Control System

```
CSPROJECTREMOVE  {-P:ALL | -P:Specific Project name  -T: WebXPanel | -T:MobileApp  -U:TB | -U:AU }  
	 -P: Remove a specific project or ALL.  Must be specified. 
	 -T: Project type 'WebXPanel' or 'MobileApp' 
	 -U: The console command requestor ID, 'TB' - toolbox or 'AU' - Autoupdate
```

### CSPROJECTload

**Role:** Programmer | **Description:** Load the project in Control System

```
CSPROJECTLOAD { -P:Specific Project name  -T: WebXPanel | -T:MobileApp  -U:TB | -U:AU   }
		  -P:  Load a specific project or  no parameter Show current installed projects 
		  -T:  Project type 'WebXPanel' or 'MobileApp'. Optional for CH5Z projects to be loaded as both mobile app and xpanel project
		  -U: the console command requestor ID, 'TB' - toolbox or 'AU' - Autoupdate
```

### CWSANTICSRF

**Role:** Administrator | **Description:** Enables/disables Anti-csrf feature

```
CWSANTICSRF [ON | OFF]
CWSANTICSRF [ON] Enables CWS Anticsrf feature
CWSANTICSRF [OFF] Disables CWS Anticsrf feature
	No parameter - displays current setting
```

### CWSBASICAUTHentication

**Role:** Administrator | **Description:** Enables/disables CWS Basic Authentication feature

```
CWSBasicAuthentication [ON | OFF]
CWSBasicAuthentication [ON] Enables CWS Basic Authentication feature on 4-series CS.
CWSBasicAuthentication [OFF] Disables CWS Basic Authentication feature on 4-series CS.
	No parameter - displays current setting
```

### DATASTOREDELete

**Role:** Programmer | **Description:** Clear the Logs for the Specified Program

```
DATASTOREDELETE [-T:DAYS OLD] [-P:ALL | -P:Specific OWNER ID] [-L | -G] 
	-T: Delete older than xxx days 
	-P: Clear DATASTORE for a specific owner or ALL.
	-L: Operate on Local Store
	-G: Operate on Global Store
```

### DATASTOREEXPORT

**Role:** Administrator | **Description:** Export to XML file

```
DATASTOREEXPORT [-F:filename] [-P:ALL | -P:Specific OWNER ID] [-L | -G]
	-F:\filepath\filename for result. Default is Console
	-P: Export DATASTORE records for a specific owner or ALL.
	-L: Operate on Local Store
	-G: Operate on Global Store
```

### DATASTOREIMPORt

**Role:** Operator | **Description:** Import from XML file

```
DATASTOREIMPORT [-F:filename] [-L | -G]
	-F:\filepath\filename to import. Default is Console
	-L: Operate on Local Store
	-G: Operate on Global Store
```

### DATASTORESTATus

**Role:** Operator | **Description:** The Data Store Status

```
DATASTORESTATUS
Gives Information on All data Store databases.
```

### DATASTreamstats

**Role:** Operator | **Description:** Printing stream statistics

```
Usage: DATASTreamStats
```

### DBGDEVice

**Role:** Operator | **Description:** (*) Simulate incoming packets for the sleected device

```
DBGDEVICE[:program#] {devnum} {packet} {-L}  - Simulate an incoming packet {packet} for device {devnum}
	program#: number of program to execute. (default=1)
	  {devnum} is a Hex number (i.e. 0x0014) or a decimal number (i.e. 20)
	  {packet} is a Quoted string representation of a packet without an ID or count
	        (i.e. "\x00\x01\x80" represents a digital low for join 1)
	  -L means the packet should be treated as a long packet.
```

### DBGMGR

**Role:** Programmer | **Description:** Enable/Disable Debug for a given Manager

```
DBGMGR <manager> <feature> <ON|OFF>
	  MSG 
	  MEMORYMANAGER 
	  HARDKEYMANAGER
```

### DBGPKTRX

**Role:** Operator | **Description:** (*) Custom App Rx Debug.

```
DBGPKTRX[:program#] {Parameters}
	program#: number of program to execute. (default=1)
	-S:ON|OFF     Turn ON or OFF display of RX packets (Current: OFF)
	-N:C|E|S|A    Show for Cresnet, Ethernet, Slot, or All [All assumed if not present] (Current: Invalid)
	-I:ID		    ID to debug; Preface with 0x for Hex.  Assumes all ID's if not present (Current: ID 0x00, 0)
	-H:ON|OFF	    Show packets as hex only (Current: OFF)
	-T:ON|OFF	    Timestamp (Current: OFF)
	-Z:ON|OFF     Show packets with zero as the ID (Current: OFF)
```

### DBGPKTTX

**Role:** Operator | **Description:** (*) Custom App Tx Debug.

```
DBGPKTTX[:program#] {Parameters}
	program#: number of program to execute. (default=1)
	-S:ON|OFF     Turn ON or OFF display of TX packets (Current: OFF)
	-N:C|E|S|A    Show for Cresnet, Ethernet, Slot, or All [All assumed if not present] (Current: Invalid)
	-I:ID		    ID to debug; Preface with 0x for Hex.  Assumes all ID's if not present (Current: ID 0x00, 0)
	-H:ON|OFF	    Show packets as hex only (Current: OFF)
	-T:ON|OFF	    Timestamp (Current: OFF)
	-Z:ON|OFF     Show packets with zero as the ID (Current: OFF)
```

### DBGSIGnal

**Role:** Operator | **Description:** (*) Set/view Debug flags and signal values

```
DBGSIGNAL[:program#] {Parameters}
	program#: number of program to execute. (default=1)
	DBGSIGNAL RESET               - Turn off all debug flags (Global, Signal specific, and Ignore)
	DBGSIGNAL ALL ON              - Turn on Global debug flag
	DBGSIGNAL ALL OFF             - Turn off Global debug flag
	DBGSIGNAL ALL SHOW            - Show global & signal debug status
	DBGSIGNAL ALL SYNC            - Write values of non-zero digital & analog signals, non-transient serial strings
	DBGSIGNAL TIME ON             - Turn on show time in ticks
	DBGSIGNAL TIME OFF            - Turn off show time in ticks
	DBGSIGNAL {signum} ON         - Turn on signal-specific debug flag for signal {signum}
	DBGSIGNAL {signum} OFF        - Turn off signal-specific debug flag for signal {signum}
	DBGSIGNAL {signum} SHOW       - Show status of signal-specific debug flag & ignore flag for signal {signum}
	DBGSIGNAL {signum} SYNC       - Show value of signal {signum}
	DBGSIGNAL {signum} IGNORE ON  - Turn on ignore-global debug flag for signal {signum}
	DBGSIGNAL {signum} IGNORE OFF - Turn off ignore-global debug flag for signal {signum}
	  {signum} is a Hex number (i.e. 0x0014) or a decimal number (i.e. 20)
```

### DBGTRANSMITTER

**Role:** Operator | **Description:** (*) Set/Clear IR/RF Transmitter Debug flag

```
DBGTRANSMITTER[:program#]
	No parameters - Current state
```

### DEBUGPROGram

**Role:** Programmer | **Description:** Configure debugging for SIMPL# Pro programs.

```
DEBUGPROGram [-P: Program Number [-C | -IP: Client IP or Hostname -Port: Debug Port]] [-D] [-S] 
	 -P:     Number of the application to debug. Ex. -P:2 to configure the debug configuration of program two.
	 -IP:    IP Address of Hostname of the debugging client that will attach to the program. '0.0.0.0' can be specified to allow any client to connect.
	 -Port:  Port number to connect on.
	 -D:     Do not port forward debug connection to LAN side. Available on CS side only. Applies to adding and clearing.
	 -S:     Start the program in suspended state waiting for the debugging client to attach.
	 -C:     Clear Debug information for the specified program
	 -?:     Print help information
	 No Parameters: Print current debug configuration information.
```

### DEBug

**Role:** Operator | **Description:** Set/View run-time debug options

```
Valid options are:
 CONsole - via current console
 DISable - all debugs OFF
 ASCII -  ASCII only
 MIXED -  ASCII and hex
 HEX_ONLy -  hex, no ACSII
 HEX -  hex with space
 NO_ZERoes -  skip zeroes
 ALL_HEX -  all hexadecimal
 SER_DATa -  serial data only
 SINGLe_id - single cresnet ID
 POWERUP - powerup ON|OFF
 ON - all or powerup
 OFF - all or powerup
 SAVE - save in EEPROM
 LEVel - set debug level(0-3)
 	syntax: debug # ON|OFF [lev #]
 HELP - show levels bitmap
   Status if no arguments

 #0 bitmap:

To use debug:
   - enable debug output: DEBUG [CONSOLE]
   - specify what to debug(run DEBUG with no parameters for opt#): DEBUG opt# [ON|OFF] 
   - to kill all debugs: DEBUG OFF
   - to restore or clear settings after powerup(does autosave): DEBUG POWERUP [ON|OFF]
   - to save manually debug conf(DEBUG OFF does not autosave): DEBUG SAVE
```

### DEFRouter

**Role:** Administrator | **Description:** Set default router

```
DEFROUTER [device_num ip_address]
	ip_address - IP address in dot decimal notation
	device_num - specified Ethernet device
	/now - take effect without a reboot
	No parameter - displays current value
```

### DELETEAUTHDOMain

**Role:** Administrator | **Description:** Delete a configured authentication domain

```
DELETEAUTHDOMAIN [-A:admin_account [-P:admin_password]] domain_name
where
   -A:admin_account - domain administrator account to use when deleting the device account
   -P:admin_password - password for the admin_account
Account credentials are not needed for domain types other than 'AD'
   domain_name - specifies the name of the authentication domain to delete
```

### DELETEDOMAINGroup

**Role:** Administrator | **Description:** Delete an existing domain group

```
DELETEDOMAINGROUP groupname [/Y]
	domaingroupname - name of the domain group (domain\groupname) to be deleted.
```

### DELETEGroup

**Role:** Administrator | **Description:** Delete an existing local group

```
DELETEGROUP groupname [/Y]
	groupname - name of the group to be deleted.
```

### DELETEUser

**Role:** Administrator | **Description:** Delete an existing local user

```
DELETEUser username [/Y]
	username - name of the user to be deleted.
```

### DELete

**Role:** Programmer | **Description:** Remove File(s)

```
DELETE filesearchstring
	filesearchstring - search string which may contain wildcards
```

### DHCP

**Role:** Administrator | **Description:** Control dynamic IP addressing

```
DHCP [device_num  [ON | OFF | REL_RENEW]] [/now]
	ON - enables DHCP for device_num
	OFF - disables DHCP for device_num
	REL_RENEW - performs a DHCP release and renew for device_num
	/now - takes effect without a reboot
	No parameter - displays current setting
```

### DHCPEx

**Role:** Administrator | **Description:** Control dynamic IP addressing

```
DHCP [device_num  [ON | OFF | REL_RENEW]] [/now]
	ON - enables DHCP for device_num
	OFF - disables DHCP for device_num
	REL_RENEW - performs a DHCP release and renew for device_num
	/now - takes effect without a reboot
	No parameter - displays current setting
```

### DHCPOpt

**Role:** Administrator | **Description:** Use FQDN in DHCP Discover Request

```
DHCPOpt [HOSTNAME | FQDN]
	HOSTNAME - Send Local HostName in DHCP Discover Request
	FQDN - Send the Fully Qualified Domain name in Discover Request - Default Option
	No parameter - displays current setting
```

### DIR

**Role:** Operator | **Description:** List files and directories in current directory

```
DIR filesearchstring
	filesearchstring - search string which may contain wildcards
```

### DISABLEDEFAULTPROGram

**Role:** Programmer | **Description:** Get or Set Current DefaultProgram Status

```
DISABLEDEFAULTPROGRAM [Value]
	To Disable Default Program - Set Value to ON
	To Enable Default Program - Set Value to OFF
	No parameter - Displays Current Default Program Status
```

### DISABLEREBOOTOFprog0

**Role:** Operator | **Description:** Disables repeated reboot of Prog00

```
DISABLEREBOOTOFProg0 [ON | OFF]
	 [ON | OFF] - Disable/enable repeated Rebooting of Prog0
	no parameter - displays current value
```

### DOMAINNAMEEx

**Role:** Administrator | **Description:** Set domain name

```
DOMAINNAMEEX [device_num domain | /CLEAR ]
	device_num - Specified ethernet device[0..3]
	domain - ASCII string containing domain name
	/CLEAR - clears the value
	No parameter - displays current value
```

### DOMAinname

**Role:** Administrator | **Description:** Set domain name

```
DOMAINNAME [string | /CLEAR] [/now]
	string - ASCII string containing domain name
	/CLEAR - clears the value
	/now - take effect without a reboot
	No parameter - current value
```

### DUMPCOMCAPS

**Role:** Operator | **Description:** Dumps comp port HW capabilities

```
DUMPCOMCAPS [COMPORTNUMBER]
Dumps HW capabilities for the specified COMPORT.
```

### ECHo

**Role:** Operator | **Description:** Enable/disable character echoing

```
ECHO [ON | OFF]
	No parameter - displays current setting
```

### EDEBUG

**Role:** Operator | **Description:** Set/View run-time ethernet debug options

```
Valid options are:
GATEWAY [ON/OFF] - turns Gateway Server extended debugs on and off
ZPANEL [ON/OFF] - turns ZPanel Server extended debugs on and off
ESLAVE [ON/OFF] - turns eslave client debug on and off
[ON/OFF] - turns all debug on and off 

To use debug:
	 - enable all debug outputs: EDEBUG ON
	 - Specify what Logic App to debug: AENTRY [Application ID]
	 - Specify what Logic App and IPTable Entry to debug: SENTRY [Application ID] [CIP ID]
	 - Specify what Logic App to remove from debug: RAENTRY [Application ID]
	 - Specify what Logic App and IPTable Entry remove from debug: RSENTRY [Application ID] [CIP ID]
	 - To kill debugs: EDEBUG OFF
```

### ENABLEFEature

**Role:** Administrator | **Description:** Enable Disable features

```
ENABLEFEATURE <FEATURE> [ON, OFF]
	FEATURE - Feature to be enabled/disabled or ALL
	ON - start feature when system boots
	OFF - do not start feature when system boots
	feature by itself shows current state for next boot
```

### ERASE

**Role:** Programmer | **Description:** Remove file(s)

```
ERASE filesearchstring
	filesearchstring - search string which may contain wildcards
```

### ERRlog

**Role:** Operator | **Description:** Prints the current error log

```
ERRLOG {SYS | PLOGCURRENT | PLOGPREVIOUS | PLOGALL | NOTICE | WARNING | ERROR | FATAL }
	No parameter:  Display the last 500 messages with Notice severity or greater
	SYS - Show the last 500 messages
	PLOGCURRENT - print persistent log for current session
	PLOGPREVIOUS - print persistent log for previous session
	PLOGALL - print persistent log for current and previous session
	NOTICE - print all notices and above (default)
	WARNING - print all warnings and above
	ERROR - print all errors and above
	FATAL - print all fatal errors and above
```

### FANTest

**Role:** Operator | **Description:** fan test; speed/power/params

```
Usage: FANTest [--p_coeff|--i_coeff|--d_coeff|--auto|--setpoint|--scantime|--speed|-defaults|-status|-gettemp|--enabledebug] [<range values>]
	--p_coeff <0.0-5.0>:              	Set P coefficient for PID Calculation. (note: auto must be set to 1)
	--i_coeff <0.0-5.0>:             	Set I coefficient for PID Calculation. (note: auto must be set to 1)
	--d_coeff <0.0-5.0>:             	Set D coefficient for PID Calculation. (note: auto must be set to 1)
	--auto <0/1>:            	enable auto Fan(PID); 0=disable and manually adjust fan.(1=default)
	--setpoint <65>:            	enter degrees Celcius.
	--scantime <3000>:            	set scantime for PID loop,  time is in msec. 60000=1 minute.
	--speed <0-100>:         	fan speed=0-100 percent; 100=max rate
	-defaults :         	No params, will reset PID params to default.
	-status :       	No params, will display current settings of parameters.
	--enabledebug <0/1>:        	Will display settings/parm values on each pwm update.
	-gettemp :              	showtemp - show local and remote temperature of main sensor and dsp board sensor.
```

### FGETfile

**Role:** Programmer | **Description:** FTP file from a remote server

```
FGETfile {--secure} [url] [local_path] {username:password}
	--secure - if specified, website certificates will be validated
	url - fully qualified URL to the file being downloaded from the server
	local_path - destination path to the file in the ROM
	username:password - access credentials to the server
```

### FIPSMode

**Role:** Administrator | **Description:** Display or change FIPS mode

```
FIPSMode [OFF]
	'OFF' disables FIPS-compliant mode
	No parameter - displays current setting
	Use RESTORE to enable FIPS-compliant mode
```

### FORCEDREBOOT

**Role:** Operator | **Description:** Forces system reboot

```
FORCEDREBOOT - reboot system
```

### FORMAT

**Role:** Operator | **Description:** Format removeable media

```
FORMAT [index]
	index - index of the external removable memory disk to be formatted
		(e.g. if index = 2, RM2 will be formatted)
	if index not specified, RM will be formatted.
```

### FPUTfile

**Role:** Programmer | **Description:** FTP file to a remote server

```
FPUTfile [url] [local_path] {username:password}
	--secure - if specified, website certificates will be validated
	url - fully qualified URL to the file being uploaded to the server
	local_path - path to the source file in the ROM
	username:password - access credentials to the server
```

### FREE

**Role:** Operator | **Description:** Show available file space

```
FREE - Indicates free disk space
	No parameter needed
```

### GETAUDITLOG

**Role:** Administrator | **Description:** Retrieve the audit log.

```
UPLOAD AUDITLOG via XMODEM 
GETAUDITLOG
	No parameter - retrieve the audit log file via xmodem
```

### GETCODE

**Role:** Operator | **Description:** Retrieve code needed for eControl2 activation

```
GETCODE 
	 Retrieves code needed for eControl2 activation.
```

### GETIPTABLE

**Role:** Operator | **Description:** Transfer the IP table from Internal flash

```
GETIPTABLE [program]
	program - which program the table is for (default = 1)
```

### GETJOINFROMCRESNEXT

**Role:** Programmer | **Description:** Get Join from CresNext Object

```
Get Join from CresNext Object
```

### GETMULTISLOTANALOGJOIN

**Role:** Programmer | **Description:** Get a multi slotted analog join

```
Get multi slot analog join value.
GETMULTISLOTANALOGJOIN [NumSlots] [slot# ][join#]
	[slot#] - This specifies number of slots which are part of this multi slot join request 
	[slot#] - Indivual slot nos 
	[join#] - positive integer
```

### GETMULTISLOTDIGITALJOIN

**Role:** Programmer | **Description:** Get a multi slotted digital join

```
Get a multi slot digital join value.
GETMULTISLOTDIGITALJOIN [NumSlots] [slot# ][join#]
	[NumSlots#] - This specifies number of slots which are part of this multi slot join request
	[slot1... slotn#] - Individual slot nos 
	[join#] - positive integer
```

### GETMULTISLOTSERIALJOIN

**Role:** Programmer | **Description:** Get a multi slotted serial join

```
Get a multi slot serial join value.
GETMULTISLOTSERIALJOIN [NumSlots] [slot# ][join#]
	[NumSlots#] - This specifies number of slots which are part of this multi slot join request 
	[slot1 ... Slotn#] - Individual slot nos 
	[join#] - positive integer
```

### GETPAsswordrule

**Role:** Administrator | **Description:** Display password rules

```
GETPASSWORDRULE
	No parameters needed.
```

### HEARTBEATtimeout

**Role:** Administrator | **Description:** Set TCP Socket Send Timeout value in Milliseconds

```
HEARTBEATTIMEOUT [timeoutInMilliSeconds]
	timeoutInMilliSeconds - Timeout before sending a CIP heartbeat to the peer if no messages are received from the peer. Default value is 30 seconds.
	No parameter - displays current setting
```

### HELP

**Role:** Operator | **Description:** Display help screens

```
HELP [ALL|DEV|ETHER|SYS|BACNET|USER|CRESTIMERENG|DEVICE]
```

### HOSTname

**Role:** Administrator | **Description:** Set hostname

```
HOSTNAME [string | /clear] [/now]
	string - ASCII string containing host name
	/clear - clears the value
	/now - take effect without a reboot
	No parameter - current value
```

### HWDEVTest

**Role:** Operator | **Description:** HW device test options

*No detailed help available.*

### ICMP

**Role:** Administrator | **Description:** Turn ON/OFF ICMP

```
ICMPREDIRECT [Enable | Disable] 
	Enable Disable ICMP Redirect. 
	No parameter - displays current setting
```

### ICMPREDIRECT

**Role:** Administrator | **Description:** Enable/disable ICMP Redirect

*No detailed help available.*

### INFO

**Role:** Operator | **Description:** Print Software Capabilities

```
INFO
	No parameters
```

### INITIALIZE

**Role:** Programmer | **Description:** Clear file system

```
INITIALIZE
	 No parameter
```

### INTERNALCNETDebug

**Role:** Operator | **Description:** Set/View run-time Internal Cresnet debug options.

*No detailed help available.*

### IPAddress

**Role:** Administrator | **Description:** Set IP address

```
IPADDRESS [device_num ip_address] [/now]
	ip_address - IP address in dot decimal notation
	device_num - specified Ethernet device
	/now - take effect without a reboot
	No parameter - displays current value
```

### IPCONFIG

**Role:** Operator | **Description:** Display/Configure IP Settings

```
usage: ipconfig [/all | /renew [adapter index] | /release [adapter index] ] /flushdns
	 ?         Display this help message
	 /release  Release the IP address of the specified adapter
	 /renew    Renew the IP address of the specified adapter
	 /flushdns Clean the name resolution client cache
```

### IPMask

**Role:** Administrator | **Description:** Set IP subnet mask

```
IPMASK [device_num ip_address]
	ip_address - IP address in dot decimal notation
	device_num - specified Ethernet device
	/now - take effect without a reboot
	No parameter - displays current value
```

### IPROUTE

**Role:** Operator | **Description:** Print Kernel IP routing table

```
IPROUTE - display network routing table
```

### IPTable

**Role:** Operator | **Description:** Display IP Table

```
IPTABLE  [-P:program] [-T] [-I:id] [-C] [-O] 

	-I:id:  ID to display entry for
	-P:program: ALL or # of programs's IP table to show
	-T Display data in a tabular format 
	-C Clears the IP Table for the specified program. Requires -P option 
	-O Displays only offline devices 
	No Arguments shows IP Table for program 1
```

### IPV6

**Role:** Administrator | **Description:** Enable/Disable IPv6

```
IPV6 [ON|OFF]
	ON - enables IPv6 for all interfaces
	OFF - disables IPv6 for all interfaces
	No ON/OFF parameter - displays current setting
```

### IPV6AUTOFlowlabels

**Role:** Administrator | **Description:** Enable/Disable IPv6 auto flow labels

```
IPV6AUTOFlowlabels [ON|OFF]
	ON - enables IPv6 auto flow labels
	OFF - disables IPv6 auto flow labels
	No ON/OFF parameter - displays current setting
```

### IPV6Address

**Role:** Administrator | **Description:** Add or remove a static IPv6 address

```
IPV6Address [device_num] [<ADD/REMove> <address>]
	device_num - specified Ethernet device
	ADD - adds a static IPv6 address to an Ethernet device
	REMove - takes away a static IPv6 address from an Ethernet device
	address - IPv6 address including subnet prefix suffix, for example 2001:db8::1/64
	No parameter - displays current values for all Ethernet devices
	If device_num is not specified, Ethernet device 0 is implied
```

### IPV6Config

**Role:** Administrator | **Description:** Display current IPv6 settings and information

```
IPV6CONFIG
usage: IPV6CONFIG [ /all ]
	 ?         Display this help message
	 /all      Show more detailed info
```

### IPV6DAD

**Role:** Administrator | **Description:** Enable/Disable IPv6 duplicate addresss detection

```
IPV6DAD [interface] [ON|OFF]
	ON - enables IPv6 duplicate address detection for interface
	OFF - disables IPv6 duplicate address detection for interface
	No ON/OFF parameter - displays current setting for that interface
	Interface defaults to 0 if not specified
```

### IPV6DESTUnreachable

**Role:** Administrator | **Description:** Enable/Disable ICMPv6 destination unreachable messages

```
IPV6DESTUnreachable [ON|OFF]
	ON - enables ICMPv6 destination unreachable messages
	OFF - disables ICMPv6 destination unreachable messages
	No ON/OFF parameter - displays current setting
```

### IPV6DHcp

**Role:** Administrator | **Description:** Enable/Disable DHCP for IPv6

```
IPV6DHCP [device_num] <ON|OFF>
	device_num - specified Ethernet device
	ON - enables IPv6 DHCP for device_num
	OFF - disabled IPv6 DHCP for device_num
	No parameter - displays current setting
```

### IPV6Defrouter

**Role:** Administrator | **Description:** Set a static IPv6 default router

```
IPV6Defrouter [interface] <address>
	interface - Ethernet interface number, if not specified, 0 is implied
	address - IPv6 address not including subnet prefix suffix, for example 2001:db8::1, use "::" to clear the route
	No parameter - displays current value
```

### IPV6MULTIcast

**Role:** Administrator | **Description:** Enable/Disable multicast proxy for IPv6

```
ERROR: Command only supported on systems that have a router
```

### IPV6NDP

**Role:** Administrator | **Description:** IPv6 Neighbor Discovery Protocol information

```
IPV6NDP <intf> - shows Neighbor Discovery Protocol information per interface
```

### IPV6PINGResp

**Role:** Administrator | **Description:** Enable/Disable ping responses for IPv6

```
IPV6PINGRESP [ON|OFF]
	ON - enables responding to IPv6 pings
	OFF - disables responding to IPv6 pings
	No ON/OFF parameter - displays current setting
```

### IPV6REDirects

**Role:** Administrator | **Description:** Enable/Disable IPv6 redirects

```
IPV6REDirects [interface] [ON|OFF]
	ON - enables IPv6 redirects for interface
	OFF - disables IPv6 redirects for interface
	No ON/OFF parameter - displays current setting for that interface
	Interface defaults to 0 if not specified
```

### IPV6ROUTEAdd

**Role:** Administrator | **Description:** Add a static IPv6 route

```
IPV6ROUTEADD <destination> <gateway> [interface]
	destination - IPv6 network including prefix
	gateway     - IPv6 address without prefix
```

### IPV6ROUTEDelete

**Role:** Administrator | **Description:** Delete a static IPv6 route

```
IPV6ROUTEDELETE <destination> <gateway> [interface]
	destination - IPv6 network including prefix
	gateway     - IPv6 address without prefix
```

### IPV6ROUTEprint

**Role:** Administrator | **Description:** Print IPv6 routing table

```
IPV6ROUTEprint [/NAME] - shows IPv6 routes
```

### IPV6SLaac

**Role:** Administrator | **Description:** Enable/Disable SLAAC for IPv6

```
IPV6SLAAC [ifnum] <ON|OFF>
	ON - enables SLAAC for IPv6
	OFF - disables SLAAC for IPv6
	No ON/OFF parameter - displays current setting
```

### ISDIR

**Role:** Operator | **Description:** Is the parameter a directory

```
ISDIR directory
	directory - string containing directory specification
```

### ISTAT

**Role:** Operator | **Description:** (*) Check Internal Status of Program

```
ISTAT[:program#] {Parameters}
	program#: number of program to execute. (default=1)
	ISTAT SIG                   - Show internal status on signals.
	ISTAT PROG [-Q]             - Show internal status on program, -Q=Do Not List Symbols
	ISTAT SYM {number}          - Show internal status of specified symbol
	ISTAT DEV                   - Show devices in system only.
	ISTAT REGDEV                - Show successfully registered devices in system only.
	ISTAT LIST {number}         - List all occurances of compiler code {number} in the program.
	ISTAT SHOWDEBUG {number}    - Show Debug Info for symbol {number} in the program.
	ISTAT SYMQUE                - Show number of entries in symbol input queue for devices that have them.
	ISTAT PSTRINGS              - Show size of each perm. string & total space for all fixed strings.
	ISTAT TREE {number}         - Show children and helpers of this symbol.
	ISTAT ABILITY {number}      - Show abilities of this symbol.
	ISTAT MAINLOOP              - Show main loop counter.
	ISTAT OVERHEAD              - Show some symbol data overhead.
	ISTAT SCHED                 - Scheduler Dump.
	ISTAT SPLUS {TASKSTAT name} - Show SIMPL Windows S# for the given SIMPL+ TASKSTAT taskname
	ISTAT WAVELIST              - Show last symbols processed
		(Use LOGICDEBUG WAVESTORE	command to change size)
```

### JOINGETINANalog

**Role:** Operator | **Description:** Read Analog Input Joins to Console

```
Xact# slot#[.subslot#...] join#1...[join#N]
```

### JOINGETINDIgital

**Role:** Operator | **Description:** Read Digital Input Joins to Console

```
Xact# slot#[.subslot#...] join#1...[join#N]
```

### JOINGETINSErial

**Role:** Operator | **Description:** Read Serial Input Joins to Console

```
Xact# slot#[.subslot#...] join#
```

### JOINGETINTparam

**Role:** Operator | **Description:** Read Integer Params to Console

```
[type]
Xact# slot#[.subslot#...] join#1...[join#N]
```

### JOINGETOUTANalog

**Role:** Operator | **Description:** Read Analog Output Joins to Console

```
Xact# slot#[.subslot#...] join#1...[join#N]
```

### JOINGETOUTDIgital

**Role:** Operator | **Description:** Read Digital Output Joins to Console

```
Xact# slot#[.subslot#...] join#1...[join#N]
```

### JOINGETOUTSErial

**Role:** Operator | **Description:** Read Serial Output Joins to Console

```
Xact# slot#[.subslot#...] join#
```

### JOINGETSERparam

**Role:** Operator | **Description:** Read Serial Params to Console

```
Xact# slot#[.subslot#...] join#1...[join#N]
```

### JOINMONITORSlot

**Role:** Operator | **Description:** Start/Stop TJI monitor

```
JoinMonitorSlot - Valid Options are 
JoinMonitorSlot ? - Display this help 
JoinMonitorSlot - Display current list of slots being monitored 
JoinMonitorSlot [transactionId] #slot[.subslot]...  
JoinMonitorSlot STOP ALL - Remove all slots 
JoinMonitorSlot STOP [transactionId]  - Remove Specified slot
```

### JOINSETANALOG16

**Role:** Operator | **Description:** Set Analog Joins from Console for 16 bit Ethernet Id Devices

```
JOINSETANALOG16 -  Direct Signal Write.
 [type] slot#[.subslot#...] join#1=val#1 ...[join#N=val#N]
  Type could be
 TYPE01 - Sends Analog Packet
  TYPE14 - Sends New Analog Packet
  Only for 16 bit ethernet IP Id's
```

### JOINSETANalog

**Role:** Operator | **Description:** Set Analog Joins from Console

```
JOINSETANALOG -  Direct Signal Write.
 [type] slot#[.subslot#...] join#1=val#1 ...[join#N=val#N]
  Type could be
 TYPE01 - Sends Analog Packet
  TYPE14 - Sends New Analog Packet
```

### JOINSETDIGITAL16

**Role:** Operator | **Description:** Set Digital Joins from Console for 16 bit Ethernet Id Devices

```
JOINSETDIGITAL16 -  Direct Signal Write. 
 slot#[.subslot#...] join#1=val#1 ...[join#N=val#N]
 Only for 16 bit ethernet IP Id's
```

### JOINSETDIgital

**Role:** Operator | **Description:** Set Digital Joins from Console

```
JOINSETDIGITAL -  Direct Signal Write. 
 slot#[.subslot#...] join#1=val#1 ...[join#N=val#N]
```

### JOINSETINTparam

**Role:** Operator | **Description:** Send Integer Parameter from Console

```
JOINSETINTPARAM -  Direct Signal Write. 
 [type] slot#[.subslot#...] param#1=val#1 ...[param#N=val#N]

 Type could be 
 TYPE09 - Sends 16 bit Parameters
 Default are 32 bit parameters
```

### JOINSETPAcket

**Role:** Operator | **Description:** Send Any Packet from Console

```
JOINSETPACKET -  Direct Signal Write. 
 slot#[.subslot#...]["[ASCII_string]"] | [hex_byte_1...hex_byte_N]
```

### JOINSETSERIAL16

**Role:** Operator | **Description:** Send Any Packet from Console for 16 bit Ethernet Id Devices

```
JOINSET16XXX Command failed
```

### JOINSETSERParam

**Role:** Operator | **Description:** Send Serial Parameter from Console

```
JOINSETSERPARAM -  Direct Signal Write. 
 slot#[.subslot#...] param# ["[ASCII_string]]  | [hex_byte_1...hex_byte_N]
```

### JOINSETSErial

**Role:** Operator | **Description:** Send Any Packet from Console

```
JOINSETSERIAL -  Direct Signal Write. 
 [type] slot#[.subslot#...] ["[ASCII_string]"] | [hex_byte_1...hex_byte_N]
 Type could be 
 TYPE12/ type12 - Sends Multi Serial Packet
 TYPE15/ type15 - Sends Extended Serial Packet
```

### JWTALLOWSELFSIGNEdconnection

**Role:** Administrator | **Description:** Whether to use Fusion end point with self-signed certificate

```
JWTALLOWSELFSIGNEDCONNECTION 	[ENABLE/DISABLE] 
ENABLE - Allow connection to Fusion endpoint with self signed certificate
DISABLE - Do not allow connection to Fusion endpoint with self signed certificate
```

### JWTCSPALLOWurlstate

**Role:** Administrator | **Description:** Whether frame-ancestor directive of CSP allows a page from being loaded from if

```
JWTCSPALLOWURLSTATE 	[ON/OFF] 
ON - Allows page to be loaded as part of iframe.
OFF - Do not allow page to be loaded as part of iframe
No Parameter - Dispalys current setting
```

### JWTPUBLICKEYSOUrce

**Role:** Administrator | **Description:** Add Public certificate server url

```
JWTPUBLICKEYSOURCE 	 [ADD/REMOVE][SOURCE][URL][SYNC] 
  	SOURCE = Unique source string
  	URL = Url of the source from where certificate is fetched
  	SYNC = Sync the certificate for the source

Adding Source 
  JWTPUBLICKEYSOURCE ADD [SOURCE] [URL] 

Removing Source 
  JWTPUBLICKEYSOURCE REMOVE [SOURCE] 

Sync certificate for all sources 
  JWTPUBLICKEYSOURCE [SYNC]
```

### JWTPUBLICKEYSTAtus

**Role:** Administrator | **Description:** Details of the public key source

```
JWTPUBLICKEYSTATUS 
Shows if Control System is ready to accept XPanel connections authenticated by Fusion
```

### KILLSOCKET

**Role:** Administrator | **Description:** Close an active TCP console socket

```
KILLSOCKET [SHELLx]
	SHELLx - kill SHELL (SSH) console #x
```

### LIGHTBYPPN

**Role:** Operator | **Description:** start squack mode

```
Valid options are:
   Status if no arguments

Syntax: LIGHTBYPPN [4 byte Hex Adr]|ALL
```

### LIGHTSPAGE

**Role:** Operator | **Description:** (*) show lights panel page

*No detailed help available.*

### LISTAUTHDOMains

**Role:** Administrator | **Description:** List configured authentication domains

```
LISTAUTHDOMAINS - lists configured authentication domains
```

### LISTBLOCKEDips

**Role:** Administrator | **Description:** List the blocked IP addresses

```
LISTBLOCKEDip
	No parameter - display current list of blocked ip addresses
```

### LISTDNS

**Role:** Operator | **Description:** Display the list of DNS servers

```
LISTDNS
	shows current DNS servers - no parameters needed
```

### LISTDNSEx

**Role:** Operator | **Description:** Display the list of DNS servers

```
LISTDNS
	shows current DNS servers - no parameters needed
```

### LISTDOMAINGroups

**Role:** Administrator | **Description:** List existing domain groups

```
LISTDOMAINGROUPS [A] [P] [O] [U] [C]
	A: groups with administrator rights will be listed
	P: groups with programmer rights will be listed
	O: groups with operator rights will be listed
	U: groups with user rights will be listed
	C: groups with connection rights will be listed
	No parameter: all groups will be listed
```

### LISTENSTAT

**Role:** Operator | **Description:** Generate a report of the Ethernet listen sockets

```
LISTENSTAT
	 No Parameter neccessary
```

### LISTEXTERNALMODules

**Role:** Programmer | **Description:** (*) List information for python modules loaded under this program instance.

```
LISTEXTERNALMODules[:program#]
	View the current state of external modules for this program.
	No arguments necessary.
```

### LISTGROUPS

**Role:** Administrator | **Description:** List existing local groups

```
LISTGROUPS [A] [P] [O] [U] [C]
	A: groups with administrator rights will be listed
	P: groups with programmer rights will be listed
	O: groups with operator rights will be listed
	U: groups with user rights will be listed
	C: groups with connection rights will be listed
	No parameter: all groups will be listed
```

### LISTGROUPUsers

**Role:** Administrator | **Description:** List all existing (local and domain) users in an existing

```
LISTGROUPUSERS groupname
```

### LISTLOCKEDUsers

**Role:** Administrator | **Description:** List blocked users

```
LISTLOCKEDuser
	No parameter - display current list of blocked users
```

### LISTPUBKEYFromuser

**Role:** Administrator | **Description:** List existing public key from an existing user account

```
LISTPUBKEYfromuser -N:username
	-N: specifies name of a local user
```

### LISTUSERS

**Role:** Administrator | **Description:** List of users authenticated on this system

```
LISTUSERS 
	No parameter - display current list of users
```

### LOADIPTABle

**Role:** Programmer | **Description:** Load New IPTable

```
LOADIPTABLE -p:[AppId] [path]	Loads program specific DIP file from removable 
	media to the internal \sys directory 
	-P:Specific Program Identifier 
	path - path on removable media including /, 
	e.g /RM/TmpDir or /RM2/dipDir 
	Example: LOADIPTABLE -p:1 /RM/dipDir 
	Note: program MUST be restarted for new IPTABLE to take effect
```

### LOCATION

**Role:** Programmer | **Description:** Location latitude, longitude and city country.

```
Location for astronomical events 
LOCATION -LAT:Latitude -LON:Longitude -LOC:CityCountry 
	 -LAT: Latitude north <##.###> or latitude south <-##.###> 
	 -LON: Longitude east <##.###> or longitude west <-##.###> 
	 -LOC: City country
```

### LOGGER

**Role:** Programmer | **Description:** (*) Turn the logger on, off, or change the operation mode

```
LOGGER[:program#] {ON|OFF|STANDBY} {DEBUGLEVEL} {ONLY} {LOGGERMODE}
	Turn the Logger on or off
	program#: number of program to execute. (default=1)
	ON - Initialize the Logger; must specify DEBUGLEVEL.
	OFF - Disable the Logger
	STANDBY - Silence the Logger temporarily. No messages will be printed/logged. 
	{DEBUGLEVEL}- Desired Debug Level if turning Logger on. (excepted range 1-10)
	{ONLY}- Optional parameter if only one Debug Level is to be handled. 
	{LOGGERMODE} = {RM, CONSOLE, DEFAULT, RM/CONSOLE}- Optional parameter to specify the mode of the Logger.
```

### LOGGERBuffersize

**Role:** Programmer | **Description:** (*) Set or show the Logger Buffer Size

```
LOGGERBUFFERSIZE[:program#] {BUFFERSIZE}
	View or change the Logger Buffer Size
	program#: number of program to execute. (default=1)
	BUFFERSIZE - Desired Logger Buffer Size in Kilobytes(KB).
	Maximum Buffer Size Allowed: 500KB
```

### LOGGERClear

**Role:** Programmer | **Description:** (*) Clear the Logs for the Specified Program

```
LOGGERCLEAR[:program#] {ALL}
	Clear the log for the specified program.
	program#: number of program to execute. (default=1)
	{ALL} - Optional parameter to clear all the logs, including all backup logs.
```

### LOGGERDebuglevel

**Role:** Programmer | **Description:** (*) Set or show Logger debug level

```
LOGGERDEBUGLEVEL[:program#] [DEBUGLEVEL] {ONLY}
	View or change the Logger Debug Level
	program#: number of program to execute. (default=1)
	[DEBUGLEVEL] - Desired Logger Debug Level(1-10)
	{ONLY} - Include after DEBUGLEVEL to Log only this level.
```

### LOGGERFlush

**Role:** Programmer | **Description:** (*) Flush the current buffer to RM

```
LOGGERFLUSH[:program#]
	Flush the current buffer to RM
	program#: number of program to execute. (default=1)
	{No Parameters}
```

### LOGGERMode

**Role:** Programmer | **Description:** (*) View or change the Logger Mode

```
LOGGERMODE[:program#] {DEFAULT | RM | CONSOLE | RM/CONSOLE}
	View or change the Logger Mode
	program#: number of program to execute. (default=1)
	BUFFERSIZE - Desired Logger Buffer Size in Kilobytes(KB).
	Maximum Buffer Size Allowed: 500KB
```

### LOGGERNumbackuplogs

**Role:** Programmer | **Description:** (*) Set or show the Number of Backup Logs desired

```
LOGGERNUMBACKUPLOGS[:program#] {NUMBACKUPLOGS}
	View or change the desired number of backup logs for the Logger
	program#: number of program to execute. (default=1)
	NUMBACKUPLOGS - Desired number of Backup logs to keep
	Maximum number of backup files (*.bac) allowed: 10
```

### LOGGERPrint

**Role:** Programmer | **Description:** (*) Print the current log to the console

```
LOGGERPRINT[:program#] {ALL}
	Print recent messages in the Log to the console.
	program#: number of program to execute. (default=1)
	ALL - Optional parameter to print the entire log.
```

### LOGICDebug

**Role:** Operator | **Description:** (*) Set Logic debug Options

```
LOGICDEBUG {Parameters}
	                                    Current State
	LOGICDEBUG LOGIC ON|OFF               - Logic info
	LOGICDEBUG SKEDDER ON|OFF             - Event Scheduler info
	LOGICDEBUG ANSKEDDER ON|OFF           - Analog Event Scheduler info
	LOGICDEBUG VALIDATESKED ON|OFF        - Validate Scheduler Nodes
	LOGICDEBUG VALIDATESKED ON|OFF        - Validate Scheduler Nodes (Requires Custom Firmware)
	LOGICDEBUG SYMPROC ON|OFF             - Show Symbols as Processed
	LOGICDEBUG CLDL ON|OFF                - CLDL info
	LOGICDEBUG MBUFFER ON|OFF             - MBUFFER info
	LOGICDEBUG RAMP ON|OFF                - RAMP info
	LOGICDEBUG DELAY ON|OFF               - DELAY info
	LOGICDEBUG TXTIME ON|OFF              - Show time before/after packet transmission to driver
	LOGICDEBUG ABUFFER ON|OFF             - ABUFFER info
	LOGICDEBUG SMEM ON|OFF                - SMEM info
	LOGICDEBUG PRESETV ON|OFF             - PRESETV info
	LOGICDEBUG MMCLAMP ON|OFF             - MMCLAMP info
	LOGICDEBUG MMSCALER ON|OFF            - MMSCALER info
	LOGICDEBUG MSLAVE ON|OFF              - MasterSlave symbol info
	LOGICDEBUG SYMSIGPROC ON|OFF          - Show signals changed for symbols being processed

	LOGICDEBUG CLOCKDRIVER ON|OFF         - Clock Driver Debug
	LOGICDEBUG UPREQ ON|OFF               - Debug update request
	LOGICDEBUG SHOWREG ON|OFF             - Show extended registration info
	LOGICDEBUG SHOWBOOT ON|OFF            - Show extended logic startup/shutdown info
	LOGICDEBUG PAGEUPDATE ON|OFF          - Show info about Page update requests
	LOGICDEBUG BUILDIFOFFLINE ON|OFF      - Ignore m_uiOnlineState when building packet
	LOGICDEBUG TLDMTXINFO ON|OFF          - More info about built packets to TLDM
	LOGICDEBUG MEMTRACK ON|OFF            - Memory Size Tracking
	LOGICDEBUG SIGMEMTRK ON|OFF           - Memory Size Tracking
	LOGICDEBUG SENDTOTLDMTIMEOUT {time}   - Timeout sending to TLDM in ms
	LOGICDEBUG MAXWAVESINSOLUTION {size}  - Number of Waves per Logic Solution
	LOGICDEBUG MAXTRANSPERWAVE {size}     - Number of Signal transitions per wave
	LOGICDEBUG SYMQUEUEDEPTH {size}       - Depth of the Symbol Input Queue
	LOGICDEBUG SPLUSQUEUEDEPTH {size}     - Depth of SIMPL+ Symbol Input Queue
	LOGICDEBUG TRANSIENTHEAP {size}       - Transient Heap Size in bytes
	LOGICDEBUG REGTIMEOUT {time}          - Timeout for Registration Event in ms
	LOGICDEBUG ACTLOGEVENTCOUNT {number}  - Number of events to pay attention to in the Logic Activity Logger
	LOGICDEBUG ACTLOGSIZE {number}        - Size of the Logic Activity Logger
	LOGICDEBUG ACTLOGPRIORITY {priority}  - Priority of the Logic Activity Logger
	LOGICDEBUG ACTLOGSCREEN ON|OFF        - Dump Logic Activity Logger to Screen on fault
	LOGICDEBUG ACTLOGNOFILE ON|OFF        - Avoid dumping Logic Activity Logger to file on fault
	LOGICDEBUG SCHEDNODES {size}          - Number of Loopnodes in the Scheduler
	LOGICDEBUG REPORTNODES {size}         - Report if more than this number loopnodes exceeded before servicing scheduler
	LOGICDEBUG RCBCHECK {size}            - Set the number of passes before servicing analogs in the scheduler
	LOGICDEBUG TIMEREPORT {size}          - Set the number of ms required to pass before posting the time to execute RunLoopNodeCheck()
	LOGICDEBUG SHOWRMLTIME ON|OFF         - Show time between Run Main Loop
	LOGICDEBUG RMLTIME {size}             - Min Time needed to print the Run Main Loop time
	LOGICDEBUG SHOWSSQTIME ON|OFF         - Show time for Single Step Queue Solution
	LOGICDEBUG SSQTIME {size}             - Min Time needed to print the Single Step Queue Solution time
	LOGICDEBUG SHOWMSQTIME ON|OFF         - Show time for Multi Step Queue Solution
	LOGICDEBUG MSQTIME {size}             - Min Time needed to print the Multi Step Queue Solution time
	LOGICDEBUG SHOWSIQTIME ON|OFF         - Show time for Symbol Input Queue Solution
	LOGICDEBUG SIQTIME {size}             - Min Time needed to print the Symbol Input Queue Solution time

	LOGICDEBUG ALL ON|OFF                 - Turn on/off all of the above.
	LOGICDEBUG LGC ON|OFF                 - Turn on/off LOGIC, SYMPROC, SYMSIGPROC.
```

### LOGINSTAT

**Role:** Administrator | **Description:** Set time to count valid logins

```
LOGINSTAT [period]
	No parameter - Display login statistics period
	Period - time in days to count # of successful logins (1-30)
```

### LOGMESSage

**Role:** Programmer | **Description:** (*) Write a message to the log from the console

```
LOGMESSAGE[:program#] {DEBUGLEVEL} {MESSAGE}
	Write a message to the log from the console
	program#: number of program to execute. (default=1)
	DEBUGLEVEL (expected range 1-10).
	MESSAGE - String to write to log.
```

### LOGOFF

**Role:** Operator | **Description:** Logoff current user

```
LOGOFF
	No parameter needed
```

### MAKEDIR

**Role:** Programmer | **Description:** Create a Directory

```
MAKEDIR directory
	directory - string containing directory specification
```

### MDGBSIGnal

**Role:** Operator | **Description:** (*) Set/view Debug flags and signal values

```
MDBGSIGNAL[:program#] {Parameters}
	program#: number of program to execute. (default=1)
	MDBGSIGNAL -R                   - Turn off all debug flags (Global, Signal specific, and Ignore)
	MDBGSIGNAL -A:ON                - Turn on Global debug flag
	MDBGSIGNAL -A:OFF               - Turn off Global debug flag
	MDBGSIGNAL -A:SHOW              - Show global & signal debug status
	MDBGSIGNAL -A:SYNC              - Write values of non-zero digital & analog signals, non-transient serial strings
	MDBGSIGNAL -S:ON {signum(s)}    - Turn on signal-specific debug flag for signal {signum}
	MDBGSIGNAL -S:OFF {signum(s)}   - Turn off signal-specific debug flag for signal {signum}
	MDBGSIGNAL -S:SHOW {signum(s)}  - Show status of signal-specific debug flag & ignore flag for signal {signum}
	MDBGSIGNAL -S:SYNC {signum(s)}  - Show value of signal {signum}
	MDBGSIGNAL -I:ON {signum(s)}    - Turn on ignore-global debug flag for signal {signum}
	MDBGSIGNAL -I:OFF {signum(s)}   - Turn off ignore-global debug flag for signal {signum}
	  {signum(s)} is a single Hex number (i.e. 0x0014) or a decimal number (i.e. 20) or
	  a list of space separated numbers.  To specify a range, put two signum(s) separated by a colon
	  i.e. 0x14:0x20 would perform the operation for signals 0x14 through 0x20 inclusive.
	  Multiple single numbers and multiple ranges are allowed.
```

### MDNS

**Role:** Administrator | **Description:** Change nsswitch mdns configuration

```
MDNS [[-S:{OFF | ONLY | FIRST | LAST}] [-I:{4 | BOTH}]]
	'-S:OFF' - disable MDNS
	'-S:ONLY' - enable MDNS; do not use DNS if MDNS fails
	'-S:FIRST' - enable MDNS and use it first; use DNS if MDNS fails
	'-S:LAST' - enable MDNS and use it if DNS fails
	'-I:4' - restrict MDNS to IPv4 only
	'-I:BOTH' - MDNS may use both IPv4 and IPv6
	No parameter: display current setting
	Setting MDNS to 'LAST' or 'OFF' may result in leakage of link-local server names to the Internet.
	Give <domain>\<username> for domain user when prompted for username.
```

### MDNSRETURN

**Role:** Administrator | **Description:** Change nsswitch to return or not return on mdns NOTFOUND

```
MDNSRETURN [OFF | ON]
	ON - Return after mdns [NOTFOUND=return].
	OFF - Remove [NOTFOUND=return] to allow dns search after mdns.
	No parameter - displays current setting
	This command is deprecated; use MDNS instead.
	Give <domain>\<username> for domain user when prompted for username.
```

### MEMTest

**Role:** Operator | **Description:** Memory test

```
Usage: MEMTest [-s] [-k] [--memsize=<bytes>]
	-s:                     	start a Memory-Test session
	-k:                     	kill/stop the Memory-Test session currently running
	--memsize=<bytes>       	optional: specify the size of memory to test (suffix B, K, M or G is okay). Default 128M bytes
```

### MICDEVICES

**Role:** Operator | **Description:** (*) Microphone Device Info

*No detailed help available.*

### MIPTable

**Role:** Programmer | **Description:** Display Master IP Table

```
MIPTABLE [-T] 

	-T Display data in a tabular format 
	No Arguments. Shows IP Table for Master Entry
```

### MOVEfile

**Role:** Programmer | **Description:** Move a file to a different directory

```
MOVEfile sourcespec destspec 
	sourcespec - source file name specification (could be relative to current dir)
	destspec - destination file name specification (could be relative to current dir)
	filenames with embedded spaces must be enclosed in double quotes("The File")
```

### MYCRESTRON

**Role:** Programmer | **Description:** Setup MyCrestron Domain & Password, and attempt to register system.

```
Format: MyCrestron DOMAIN PASSWORD 

	 DOMAIN - sets MyCrestron domain
	 PASSWORD - sets MyCrestron password
	 No parameter - displays current setting.
```

### NETWORKSETTINGSRESET

**Role:** Operator | **Description:** Resets networking settings

```
NETWORKSETTINGRESET
	No parameter - resets network settings
```

### NEWAPIWEBTOKEN

**Role:** Operator | **Description:** (*) AVF REST api web token

*No detailed help available.*

### NUMNOHBRESPonsecnt

**Role:** Administrator | **Description:** Set maximum number of no response allowed for CIP Heartbeat Messaging

```
NUMNOHBRESPONSECNT [count]
	count - Number of times we do not receive a response to the CIP heartbeat before we close the socket. Default value is 3.
	No parameter - displays current setting
```

### NVRAMCLEAR

**Role:** Programmer | **Description:** Clear NVRAM with zeros

```
NVRAMCLEAR [-P:ALL | -P:Specific Program Identifier] [-D]
	-P: Clear NVRAM for a specific program or ALL programs. If not present, ALL assumed.
	-D: Deallocate NVRAM memory.
```

### NVRAMGET

**Role:** Operator | **Description:** Retrieve contents of NVRAM from the system

```
NVRAMGET [-P:ALL | -P:Specific Program Identifier]
	-P: Get NVRAM for a specific program or ALL programs. If not present, ALL assumed.
```

### NVRAMPUT

**Role:** Programmer | **Description:** Send contents of NVRAM to the system

```
NVRAMPUT [-P:ALL | -P:Specific Program Identifier]
	-P: Put NVRAM for a specific program or ALL programs. If not present, ALL assumed.
```

### NVRAMREBOOT

**Role:** Operator | **Description:** Print reboot information

```
NVRAMREBOOT [SHOW]
	SHOW - display the last reboot message in NVRAM
```

### OCSP

**Role:** Administrator | **Description:** Display/Set OCSP configuration for SSL communication.

```
OCSP -L:OFF|STAPLEONLY|ONLINE {-N:NumOfNonces} {-T:TimeoutInSeconds} 
	where 'OFF' is no OCSP verification,
	where 'STAPLEONLY' check certificate staple (no staple is a failure),
	where 'ONLINE' checks staple, if no staple then check validity with responder,
	where '-N:#' sets the number of nonces (currently 0 is none, any non-zero means use a nonce.)
	where '-T:#' sets the timeout in seconds to connect to responder (for ONLINE only)
	No parameter - displays current settings
```

### PACKET

**Role:** Operator | **Description:** (*) Send custom packets through the RAD tools.

```
PACKET - Creates/Sends packets
	Syntax:  PACKET [-B] [-S:C|-S:E|-S:S] [-F:form] [-P] [-I:{ID}] -[T:{Type}] {Packet Specific Data}

	Options:
	-B:  Build a packet using {packet options}
	-S:C:  Send completed packet via main cresnet
	-S:E:  Send completed packet via main Ethernet
	-S:S:  Send completed packet to a slot
	-F:form:  Use Form "form" to build the packet.
	-I:  Device ID (or list for wrapping)
	     ex:  -I:0xAA, -I:15, -I:0xAA.0xBB.0xCC (AA, BB are wrapped, CC is the inner packet)
	-T:  Packet Type
	     0x00 ("DIGITAL")    - Digital
	     0x01 ("ANALOG")     - Analog
	     0x14 ("SYMANALOG")  - Symmetric Analog
	     0x1C ("GENCFG")     - Generic Device Config
	     0x1D ("CLXRCB")     - CLX RCB
	     0x1E ("GENRCB")     - Generic RCB
	     ex:  -T:0x01 or -T:"ANALOG" to specify Analog type.
	To get {Packet Specific Data}, do "PACKET -T:{Type} ?"
```

### PASSTHRU

**Role:** Operator | **Description:** Enter passthru mode console<->device

```
Valid options are:
   any number allowed as argument
 CRESnet - cresnet device
 ETHERnet - CIP or Client/Serv
 SLOT - any sys slot
 COM - build-in com
 IR - one-way IR
 H/W - hardware handshake
 S/W - software handshake
 232 - RS232 mode
```

### PASSTO

**Role:** Operator | **Description:** Enter passto mode console<->device

```
ERROR: Bad or Incomplete Command
```

### PAUSEPROGram

**Role:** Operator | **Description:** Pauses Specified Program

```
PAUSEPROGRAM {-P:ALL | -P:Specific Program Identifier}
 	 -P:  Pause a specific program or ALL.  If not present, ALL assumed.
```

### PING

**Role:** Operator | **Description:** Ping remote node

```
Usage: ping [-ncount] [-iTTL] [-wtimeout] address
Options:
	-n count      Send count.
	-i TTL        Time to live.
	-w timeout    Timeout (in seconds)
Attention: This command has no space between option and option parameter.
```

### PPNDISCOVEr

**Role:** Operator | **Description:** Show all PPN devices on cresnet

```
PPNDISCOVER
```

### PRINTAUDITLOG

**Role:** Administrator | **Description:** Print the audit log.

```
PRINTAUDITLOG {[ALL]}
	All - Print the entire audit log
	No parameter - Print the last 50 entries from the log
```

### PROGCOMments

**Role:** Operator | **Description:** (*) Shows program Comments

```
PROGCOMMENTS[:program#]
	program#: number of program to execute. (default=1)
	No arguments necessary.
```

### PROGINFO

**Role:** Operator | **Description:** (*) Show Program Statistics

```
PROGINFO[:program#] {No arguments}
	program#: number of program to execute. (default=1)
	Shows program information.
```

### PROGLOAD

**Role:** Programmer | **Description:** Loads the specified program

```
PROGLOAD {-P:ALL | -P:Specific Program Identifier} {-N} {-D} {-X} 
 	 -P:  Load a specific program or ALL.  Must be specified.
 	 -N   If present, will not update the IP Table
 	 -D   If present, will not start the program - just register it.
 	 -X   If present, will not fail for tools/firmware compatability issues.
 	 -C   If present, will clear the module persistent data.
```

### PROGREAdy

**Role:** Operator | **Description:** Sends the program ready status

```
PROGREADY 
 	 No parameter needed - displays current program ready status
```

### PROGREGister

**Role:** Programmer | **Description:** Registers/Unregisters the specified program

```
PROGREGISTER {-P:ALL | -P:Specific Program Identifier} [-U] [-C:SSPDllName]
 	 -P:  (Un)Register the specified program or ALL
 	 -U:  if present, will unregister the program
 	 -C:  if present, indicates the entry point for a Simpl Sharp PRO program - (This is the name of the Simpl Sharp PRO DLL) 
 	 no arguments lists which programs are registered
```

### PROGRESet

**Role:** Operator | **Description:** Restarts the specified program

```
PROGRESET {-P:ALL | -P:Specific Program Identifier} {-V} {-D}
 	 -P:  Reset a specific program or ALL.  If not present, ALL assumed..
 	 -V:  Verbose reset.
 	 -D:  Don't keep DBGSIGNAL information (PROGRESET normally preserves DBGSIGNAL flags).
```

### PROGUPTIME

**Role:** Operator | **Description:** (*) Display the time the program is running

```
PROGUPTIME[:program#]
	program#: number of program to execute. (default=1)
	No arguments necessary.
```

### PROXY

**Role:** Administrator | **Description:** Configure Proxy

```
PROXY [OFF|ON] [HOST:proxy_address:port] {USER:name:password} {EXCLUDELOCAL:[OFF|ON]}
	Enclose password in double quotes " if there are spaces in the password.
	Enter "" for blank password.
PROXY SENDHOST [ON|OFF]
	No parameter - displays current setting
```

### PROXYALLOW

**Role:** Administrator | **Description:** Setup list of hosts that need to use Proxy

```
PROXYALLOW host.com;host2.edu;host4.com
	Issue "PROXYALLOW -c" to clear list
	Issue "PROXYALLOW -a hosts" to append to the list
```

### RAMFree

**Role:** Operator | **Description:** Show available RAM file space

```
RAMFree [-x]
	-x - Attribute reclaimable memory to the reclaimable field and not to free memory.
```

### RCONsole

**Role:** Operator | **Description:** Send Command to Remote console

```
rcon [cresnet] [hexID][.subslot hexSlot..]|[slot decSlot] [command string]
```

### REBOOT

**Role:** Operator | **Description:** Reboot the device

```
REBOOT - reboot system
```

### RECOVERYREBOOT

**Role:** Operator | **Description:** Forces system reboot for recovery

```
RECOVERYREBOOT - reboot system for recovery
```

### REMBLOCKEDip

**Role:** Administrator | **Description:** Remove an IP Address from the blocked list

```
REMBLOCKEDip [ALL|ipaddress]
	ipaddress - ip address of the blocked connection
	ALL - remove all blocked ip addresses
	No parameter - display current list of blocked ip addresses
```

### REMDns

**Role:** Administrator | **Description:** Remove an entry from DNS server List

```
REMDNS ip_address
	ip_address - IP address in dot decimal notation
```

### REMLOCKEDUser

**Role:** Administrator | **Description:** Remove user from the blocked list

```
REMLOCKEDuser [ALL|username]
	username - username of the blocked connection
	ALL - remove all blocked users
	No parameter - display current list of blocked users
```

### REMMaster

**Role:** Programmer | **Description:** Remove a master entry to IP table

```
Format: REMMaster cip_id ip_address/name 
	cip_id - ID of the CIP node (in hex)
	ip_address/name - IP address (IPv4 or IPv6) 
	                - or name of the site for DNS lookup
```

### REMOVEDIR

**Role:** Programmer | **Description:** Remove a Directory

```
REMOVEDIR directory 
	directory - string containing directory specification
```

### REMOVEPUBKEYFromuser

**Role:** Administrator | **Description:** Remove an existing public key from an existing user account

```
REMOVEPUBKEYfromuser -N:username
	-N: specifies name of a local user
```

### REMOVEUserfromgroup

**Role:** Administrator | **Description:** Remove an existing local or domain user from an existing local group

```
REMOVEUSERFROMGROUP -N:username -G:groupname
	-N: specifies name of a local or domain user
	-G: specifies name of a local group
```

### REMPeer

**Role:** Programmer | **Description:** Remove a peer(slave) entry to IP table

```
Format: REMPeer cip_id ip_address/name [-D:device_id] [-C:cipport] [-P:program] [-U:RoomId]
	cip_id - ID of the CIP node (in hex)
	ip_address/name - IP address (IPv4 or IPv6) 
	                - or name of the site for DNS lookup
	RoomId  - Upto 32 characters. Valid characters are A-Z and 0-9.
	               -	This is used for communication with a Virtual Control server
	device_id       - ID in device redirection table (in hex) (must be < 256)
	port number     - port number for the connection (in dec) (must be > 256)
	program         - program number which uses device (in dec) (default 1)
```

### REPORTCRESNET

**Role:** Operator | **Description:** Show all devices on the main cresnet leg

```
REPORTCRESNET  [<HEX ID>] | [ALL]
 Display all cresnet devices / Single cresnet device
```

### REPORTPPNTABLe

**Role:** Operator | **Description:** print PPN table, if any

```
0 entries found
```

### RESETPHy

**Role:** Operator | **Description:** Reset PHY, may not work on all products.

```
Usage: RESETPHy  **Note this command will not work on all products, added for CP4.
--You may need to re-establish connection-- 
TIMEOUT on TESTLOGIn
TIMEOUT on TESTLOGOut
TIMEOUT on TESTWATCH
TIMEOUT on THREADPOOLINFO
TIMEOUT on TIMEREVENTMAXQueuesize
TIMEOUT on TIMEZone
TIMEOUT on TIMEdate
TIMEOUT on TLS13CIPHER
TIMEOUT on TLSCIPHER
TIMEOUT on TLSVERsion
TIMEOUT on TOP
TIMEOUT on TRACEROUTE
RESETPassword ?
RESETPASSWORD -N:username {-P:defaultpassword}
	-N: specifies name of the user to be reset
	-P: specifies the default password
Update request from IP-ID-04 in Program 01
```

### RESETPassword

**Role:** Administrator | **Description:** Reset an existing local user's password

*No detailed help available.*

### RESTORe

**Role:** Administrator | **Description:** Restore factory defaults

```
RESTORE
	 No parameter
```

### RESUMEPROGram

**Role:** Operator | **Description:** Resumes Specified Program

```
RESUMEPROGRAM {-P:ALL | -P:Specific Program Identifier}
 	 -P:  Resume a specific program or ALL.  If not present, ALL assumed.
```

### RJSTATUS

**Role:** Programmer | **Description:** Retrieve RJ requested status

```
shows Reserve Join sttus
RJSTATUS [Reserve Join Number]
```

### RMLOGerr

**Role:** Operator | **Description:** Enable logging errors to the file.

```
RMLOGERR
 [OFF|ON] -F: {Filename} -S:{MaxSize} -N:{MaxNumOfFiles} {OK | INFO | NOTICE | WARNING | ERROR | FATAL}
	-F:{Filename}: Filename is name of the Log file (must include the path and '.log' as file extension)
 	-S{MaxSize}: MaxSize is between 262144 and 5242880 bytes
 	-N{MaxNumOfFiles}: MaxNumOfFiles is between 1 and 10
 	OK - log to file all OKs and above
 	INFO - log to file all info messages and above
 	NOTICE - log to file all notices and above
 	WARNING - log to file warnings and above
 	ERROR - log to file errors and above
 	FATAL - log to file fatal errors and above
```

### RMTRANSfer

**Role:** Programmer | **Description:** Transfer a project to/from removable media

```
RMTRANSFER {-P:Specific Program Identifier} FROM|TO path {IPT}
	FROM|TO - indicates whether transfering from/to removable media
	path - path for the project on removable media. (/rm/simpl/appXX) 
	IPT - Copy the IPTABLE also if exists
	Note: program MUST be stopped to transfer
```

### ROUTEADD

**Role:** Administrator | **Description:** Add a static IP route

```
ROUTEADD <destination> <netmask> <gateway> [/FORCE]
	destination - destination IP address in dot decimal notation
	netmask     - netmask in dot decimal notation
	gateway     - gateway in dot decimal notation
	/FORCE      - force to add/delete even if failed to persist to NVRAM
```

### ROUTEDELete

**Role:** Administrator | **Description:** Delete a static IP route

```
ROUTEDELETE {<destination> <netmask> <gateway> [/FORCE]} | </ALL>
	destination - destination IP address in dot decimal notation
	netmask     - netmask in dot decimal notation
	gateway     - gateway in dot decimal notation
	/FORCE      - force to add/delete even if failed to persist to NVRAM
	/ALL        - delete all routes from NVRAM
```

### ROUTEPRINT

**Role:** Administrator | **Description:** Print Kernel IP routing table

```
ROUTEPRINT [/NAME] - shows current routes
```

### ROUTESYMSTAT

**Role:** Operator | **Description:** (*) Check connection status of route symbols

```
ROUTESYMSTAT displays crosspoint connections
	syntax: ROUTESYMSTAT [-C:ControlId] [-E:EquipId]
	Options:
	-C:  Control Id number 0-65535, displays all crosspoints for the specified Control Id
	-E:  Equipment Id number 0-65535, displays all crosspoints for the specified Equipment Id
	No Options: display all crosspoints
```

### RPRTCRESNETIDBYPPn

**Role:** Operator | **Description:** Report cresnet ID by PPN

```
RPRTCRESNETIDBYPPN [4 Byte Hex PPN Number]
```

### RPRTPPNBYCRESNETId

**Role:** Operator | **Description:** Report PPN by cresnet ID

```
RPRTPPNBYCRESNETID [Cresnet Id in Hex]
```

### SDEBUG

**Role:** Operator | **Description:** (*) Check connection status of route symbols

```
SDEBUG[:program#] arguments

	program#: number of program to execute. (default=1)
	-D[ON|OFF]:  Set device to have it's debug info printed (ON) or not (OFF).  Followed by a space and:
	  R  :  Turn on/off debug flag for all registered devices.
	  A  :  Turn on/off debug flag for all devices.
	  C  :  Turn on/off debug flag for all top-level Cresnet devices.
	  C##:  Turn on/off debug flag for Cresnet ID ##.
	  E  :  Turn on/off debug flag for all top-level Ethernet devices.
	  E##:  Turn on/off debug flag for Ethernet ID ##.
	  S  :  Turn on/off debug flag for all top-level Slots.
	  S##:  Turn on/off debug flag for Slot ##.
	  D##:  Turn on/off debug flag for Device ##.
	    Note:  ISTAT DEV or ISTAT REGDEV can be used to list device numbers.

	  ex:  SDEBUG -DON C0x25 turns on debug flag for Cresnet ID 25
	  Dotted notation is valid for C, E, S commands above, i.e.:
	    SDEBUG -DON C0x25.A turns on debug flag for Cresnet ID 25, Port A
	    SDEBUG -DON S9.0x25.A turns on debug flag for Slot 9, ID 0x25, Port A
	-TXR[ON|OFF]:  Show transmitted packets in raw form.
	-TXI[ON|OFF]:  Show transmitted packets in interpreted form.
	-TXF[0|1]   :  Transmit Interpreted form: 0=Machine Parseable, 1=Human Readable.
	-RXR[ON|OFF]:  Show received packets in raw form.
	-RXI[ON|OFF]:  Show received packets in interpreted form.
	-RXF[0|1]   :  Receive Interpreted form: 0=Machine Parseable, 1=Human Readable.
	-PR[ON|OFF] :  Show ASCII characters in Raw Packets.
	-PI[ON|OFF] :  Show ASCII characters in Interpreted packets.

	-SB[ON|OFF] :  Suppress printing of broadcast packets.
	-SU[ON|OFF] :  Suppress printing of unresolvable packets (direct-to-wire packets going to an ID
	               not in the program).
	-O[ON|OFF]  :  Show Online/Offline Interpeted Messages.  Note that Online/Offline messages
	               will show regardless if interpretation is on.

	-S[0|1]     :  Show current settings, 0:Machine Parseable, 1:Human Readable.
	-QP[#]      :  Set quick-profile #; if #=?, show QP formats.

	-CON[ON|OFF]:  Write debug output to console
	-RM[ON|OFF|<drive num>] :  Write debug output to Removable Media
	-SZ{size}   :  Set RM Log File Size maximum
	-ST[ON|OFF] :  Show Time before packet
	-SD[ON|OFF] :  Show Date when Time is printed

	NOTE:  A device *MUST* be in the currently running program in order to be debugged!
```

### SECURECIPport

**Role:** Programmer | **Description:** Set the secure (SSL) port number for CIP

```
SECURECIPPORT [portnumber]
	portnumber - desired port number > 4095 (in decimal).
	No parameter - displays the current value
```

### SECUREGatewaymode

**Role:** Administrator | **Description:** Set/Display secure gateway operation mode.

```
SECUREGATEWAYMODE [DEFAULT | SECUREONLY | SECURENONCS | SECUREEXT]
	DEFAULT     - Accept both secure and unsecure Gateway CIP connections on all network interfaces.
	SECUREONLY  - Accept only secure Gateway CIP connections on all network interfaces.
	SECURENONCS - Accept only secure Gateway CIP connections from non control subnet.
	              Accept both secure and unsecure Gateway CIP connections on the control subnet ( Router Only Control Systems).
	SECUREEXT   - Accept only secure Gateway CIP connections from external IP addresses (from different subnets than any of the connected networks)
	No parameter - displays current Secure gateway mode settings.
```

### SECUREWEBSocketport

**Role:** Programmer | **Description:** Set secure Websocket port

```
SECUREWEBSOCKETPORT [OFF | ON | PORTNUMBER]
 portnumber - desired port number > 4096 (in decimal)
 No parameter - displays current value
```

### SECUREWebport

**Role:** Administrator | **Description:** Set Secure(SSL) port number for Web.

```
SECUREWEBPORT [portnumber]
	portnumber - desired port number  (in decimal).
	No parameter - displays the current value
```

### SENDCNETPKT

**Role:** Operator | **Description:** Send a Cresnet Packet

```
SENDCNETPKT {Parameters}
	SENDCNETPKT {data (w/o count)}   - Send a Cresnet packet.
	data is a string of 2-digit hex bytes.
	For example: ")SENDCNETPKT 03000000\r" sends a digital high to join 1 on ID 3.
 SendCresnetPacket: Packet sent successfully
```

### SENDIPTABLE

**Role:** Programmer | **Description:** Transfer the IP table to Internal flash

```
SENDIPTABLE [program]
	program - which program the table is for (default = 1)
```

### SETCRESNETIDBYPPn

**Role:** Operator | **Description:** Set cresnet ID by PPN

```
Valid options are:
   Status if no arguments

Syntax: SETCRESNETIDBYPPN [HEX cnet ID] [HEX 4-byte Address | ALL ]
```

### SETCSAUTHENTICATION

**Role:** Administrator | **Description:** Set Control System Authentication credentials.

```
SetCSAuthentication -N:Username -P:Password 
Sets Control System Authentication parameters for CIP connect message. 
	 -N: specifies name of a local or domain (domain\user) user
	 -P: specifies password.
```

### SETLOCKOUTTIME

**Role:** Administrator | **Description:** Set time that an IP is blocked from login

```
SETLOCKOUTTIME [number]
	number - number of hours (suffix 'h') or minutes (suffix 'm') to block an IP Address, 0 is indefinite, 750 hours or 45000 minutes max
	No parameter - display current setting.
```

### SETLOGINAttempts

**Role:** Administrator | **Description:** Set the number of login attempts before blocking IP

```
SETLOGINAttempts [number]
	number - number of login attempts a user will have before the console is blocked. 0 is infinite.
	No parameter - display current setting.
```

### SETLogoffidletime

**Role:** Administrator | **Description:** Set idle time allowed before current user is automatically logged off

```
SETLOGOFFIDLETIME [minutes]
	minutes - idle minutes passed before current user is logged off (Limit 60 minutes). 0 means user will NOT be logged off automatically. 
	No parameter - display current transport setting.
```

### SETMULTISLOTANALOGJOIN

**Role:** Programmer | **Description:** Process a multi slotted analog join

```
Process a multi slotted analog join.
SETMULTISLOTANALOGJOIN [Num slots ] [slot1 ] [slot2] ... [slotn] [join#] [join value]
	[Num slots#] - This specifies number of slots which are part of this multi slot join request 
	[slot1 .. slotn#] - Individual slot nos 
	[join#] - positive integer
	[join value]
```

### SETMULTISLOTDIGITALJOIN

**Role:** Programmer | **Description:** Process a multi slotted digital join

```
Process a multi slotted digital join.
SETMULTISLOTDIGITALJOIN [Num slots ] [slot1 ] [slot2] ... [slotn] [join#] [join value]
	[Num slots#] - This specifies number of slots which are part of this multi slot join request 
	[slot1 .. slotn#] - Individual slot nos 
	[join#] - positive integer
	[join value]
```

### SETMULTISLOTSERIALJOIN

**Role:** Programmer | **Description:** Process a multi slotted serial join

```
Process a multi slotted serial join.
SETMULTISLOTSERIALJOIN [Num slots ] [slot1 ] [slot2] ... [slotn] [join#] [join value]
	[Num slots#] - This specifies number of slots which are part of this multi slot join request 
	[slot1 .. slotn#] - Individual slot nos 
	[join#] - positive integer
	[join value]
```

### SETPAsswordrule

**Role:** Administrator | **Description:** Set password rules

```
SETPASSWORDRULE {-ALL | -NONE} | {-LENGTH:minPasswordLength} {-MIXED} {-DIGIT} {-SPECIAL}
	-ALL: all rules will be applied.
	-NONE no rule will be applied.
	-LENGTH: specifies minimum password length if greater than 6.  By default, the minimum length is 8. This parameter can't be combined with NONE.
	-MIXED: password must contain a lower and upper case character. This parameter can't be combined with NONE.
	-DIGIT: password must contain a number. This parameter can't be combined with NONE.
	-SPECIAL: password must contain a special character. This parameter can't be combined with NONE.
	-CHANGE: specifies minimum number of positions in a new password to change. By default, the number is 0 (disabled). This parameter can't be combined with NONE.
```

### SETPPNBYCRESNETId

**Role:** Operator | **Description:** Set PPN by cresnet ID

```
Valid options are:
   Status if no arguments

Syntax: SETPPNBYCRESNETID [HEX cnet ID] [4 byte Hex Adr]
```

### SETPPNBYPPn

**Role:** Operator | **Description:** Change old PPN to new PPN

```
Valid options are:
   Status if no arguments

Syntax: SETPPNBYPPN [Hex OldAdr]|ALL [HEX NewAdr]
```

### SETSIGnal

**Role:** Operator | **Description:** (*) Set the state of a signal in the program

```
SETSIGNAL[:program#] signal_number value {-U}
	program#: number of program to execute. (default=1)
	signal number - Hex Number (i.e. 0x0000000B) or Decimal number (i.e. 11)
	value         - 0 or 1 for Digital
	              - pXX : Pulse XX ms long for Digital
	              - iXX : Inverse pulse XX ms long for Digital
	              - 0 to 65535 for Analog
	              - Quoted string for Strings
	-U            - Assumes UTF-16 encoding of the string (default ASCII).
```

### SETUSERLOCKOUTTime

**Role:** Administrator | **Description:** Set time that a user is blocked from login

```
SETUSERLOCKOUTTIME [number]
	number - number of hours (suffix 'h') or minutes (suffix 'm') to block a User, 0 is indefinite, 750 hours or 45000 minutes max, or -1 to restore the default value
	No parameter - display current setting.
```

### SETUSERLOGINATtempts

**Role:** Administrator | **Description:** Set the number of login attempts before blocking User

```
SETUSERLOGINAttempts [number]
	number - number of login attempts a user will have before the console is blocked. 0 is infinite, or -1 to restore the default value.
	No parameter - display current setting.
```

### SHOWEXtraerrors

**Role:** Operator | **Description:** Enables/disables Show Extra Command

```
SHOWEXTRAERRORS [{option}] [OFF | ON]
	{option}  [OFF | ON] turns on or off specified option
		Px - extra for Program x on (x = program number)
		SYS - extra for general system information
		ENET - extra for ethernet communications
		BAC - extra for BACnet communications
		CRESTIMERENG - extra for Crestron Timer Engine
		AUTOUPDATE - extra for Crestron Auto Updater
		WEB - extra for Crestron Web Scripting (IIS/ISAPI)
	OFF - turns all off
	ON - turns all on
	No parameter - displays current setting
```

### SHOWHW

**Role:** Operator | **Description:** Display hardware configuration

```
SHOWHW 
 No parameters
```

### SIGDEBUG

**Role:** Administrator | **Description:** (*) List Sig information for the specified device.

```
SIGDEBUG[:program#] -T:[Transport] -I:[DeviceID].{[Subslot(s)]}
	-T:E|C|S     Device is apart of Ethernet, Cresnet, or an internal Slots.
	-I:ID        ID of the device with optional subslots. Ex: 3.1.1.
```

### SIGNALTIMESTAMP

**Role:** Administrator | **Description:** (*) Show signal timestamps

```
SIGNALTIMESTAMP -S:SigNum
	  SigNum:  Signal Number to show timestamps of.
```

### SNMP

**Role:** Administrator | **Description:** Enable/disable Simple Network Management Protocol

```
SNMP	[ON]  - Turns SNMP on
SNMP	[OFF] - Turns SNMP off
SNMP	[WIPE]    - Clears configuration
	No parameter- displays current setting
```

### SNMPALLowall

**Role:** Administrator | **Description:** Allows All SNMP Managers

```
SNMPALLOWALL 	[ON/OFF] 
Where ON = Allows All Managers
Where OFF = Allows Only Permitted Managers

No parameter- displays current setting
```

### SNMPAccess

**Role:** Administrator | **Description:** Configure Access Rights for SNMP Communities

```
SNMPAccess	[COMMUNITY] [PARAM] [-a:SecurityType -p:password [-e:PrivacyType [-k:key] ] ]
	Where PARAM = ReadOnlyAccess, ReadWriteAccess
	      securityType = MD5,SHA,SHA224,SHA256,SHA384,SHA512 
	      PrivacyType = DES,AES,AES192,AES256 
	
No parameter- displays current setting
```

### SNMPCONTAct

**Role:** Administrator | **Description:** Displays Snmp contact information

```
SNMPCONTACT 
No Parameter- Displays snmp contact information
```

### SNMPLOCATion

**Role:** Administrator | **Description:** Displays Snmp location information

```
SNMPLocation 
No Parameter- Displays snmp location
```

### SNMPMANager

**Role:** Administrator | **Description:** Configure an SNMP manager

```
SNMPMANager	[ADD/REMOVE] [NAME] [COMMUNITY NAME] [ADDRESS/HOSTNAME] [PARAMS]
Where PARAMS = one of:
NoAuthNoPriv-v1, NoAuthNoPriv-v2,NoAuthNoPriv-v3,AuthNoPriv-v3,AuthPriv-v3
Auth = authentication, Priv = privacy

To Add Manager:
SNMPManager ADD [NAME] [COMMUNITY NAME] [ADDRESS/HOSTNAME] [PARAMS]

To Remove Manager:
SNMPManager REMOVE [NAME]
	
No parameter- displays current setting
```

### SNMPMONitor

**Role:** Administrator | **Description:** Configure SNMP Monitoring and trap generation

```
SNMPMonitor ADD [OID] [COMP] [VALUE] [DESC]
	OID: Object Identifier to monitor
	COMP: Comparator EQUALS, LESSTHAN or GREATERTHAN
	VALUE: Value to compare against
	DESC: Simple text description of this probe (no spaces, 200 max.)

	The 5th parameter cannot have spaces unless enclosed in parentheses

To Remove Monitor:
SNMPMonitor REMOVE [OID]
	
No parameter- displays current setting
```

### SNMPTrap

**Role:** Administrator | **Description:** Send an SNMP trap

```
SNMPTrap	[ON/OFF] [NUM] [STRING]
ON = Traps are enabled
OFF = Traps are disabled
```

### SNTP

**Role:** Administrator | **Description:** Configure network time synchronization

```
SNTP [START|STOP|SYNC|LOG|NOLOG|DELETE {SERVER|SERVER2|SERVER3}|SERVER {args}|SERVER2 {args}|SERVER3 {args}] 
	START  - start synchronization
	STOP   - stop synchronization
	SYNC   - force synchronization (one time)
	LOG    - enable logging of SNTP messages to syslog
	NOLOG  - disable logging of SNTP messages to syslog
	DELETE {SERVER|SERVER2|SERVER3}  - delete configuration for NTP server1 or server2 or server3
	SERVER:{address} [optional args] - address of primary NTP server with optional arguments
	SERVER2:{address} [optional args]- address of secondary NTP server to synchronize with optional arguments
	SERVER3:{address} [optional args]- address of secondary NTP server to synchronize with optional arguments
	  optional args:
	   PORT:{1-65535} - NTP Port (Default 123)
	   AUTH:{MAC} - Secured NTP. MAC authentication. 
	   KEYTYPE:{MD5(less secured)|SHA1|SHA256} - Key Type for MAC authentication only. (Default SHA1). 
	   KEY:{shared key} - Pre-Shared key between NTP client and server. (MAC authentication only). 
	   KEYID:{1-65535} - Pre-Shared key index between NTP client and server. (MAC authentication only). 
	   NOTE: MD5 is not allowed when FIPSMODE is on.
	   Example: 
	    1. SNTP SERVER:macntp.example.com AUTH:mac KEYID:1 KEY:e5fa44f2b31c1fb553b6021e7360d07d5d91ff5e
	    2. SNTP SERVER:pool.example.com 
	    3. SNTP SERVER:2001:db8:be:ef:10::20
	No parameter - displays current setting
```

### SOCKETSendtimeout

**Role:** Administrator | **Description:** Set TCP Socket Send Timeout value in Milliseconds

```
SOCKETSENDTIMEOUT [value]
	value - desired timeout in milliseconds
	No parameter - displays current value
```

### SPLUSLoad

**Role:** Operator | **Description:** (*) Test loading a SIMPL+ module

```
SPLUSLOAD[:program#] splus_module_dll_name
	program#: number of program to execute. (default=1)
	splus_module_dll_name - filename of the splus DLL to load
```

### SPSHOWPOOLERR

**Role:** Operator | **Description:** (*) Show Smart Thread Pool Error.

```
SPSHOWPOOLERR[:program#]
	Show Thread Pool Errors
```

### SSHARPAPPDEBUGport

**Role:** Programmer | **Description:** Enable/Disable and configure S# App Debug SSH port number

```
SSHARPAPPDEBUGport [OFF | ON | port number]
	[OFF | ON ] - Disables/Enables Simpl Sharp Debug. Default is OFF
	portnumber - desired port number for SSH connection (in decimal).
	no parameter - displays current value
```

### SSHARPDebug

**Role:** Administrator | **Description:** (*) Set SimplSharpPro Debugs

```
SSHARPDebug[:program#] {Parameters}
	APPTOTLDMSENDMESSAGETIMEOUT time          10000    Timeout for sending messages to the TLDM in ms
	TLDMTOAPPSENDMESSAGETIMEOUT time          10000    Timeout for receiving messages from the TLDM in ms
	SENDTOTLDMTIMEOUT time                    20000    Timeout for SendToTldmEx() calls in ms
	HEARTBEAT number                             20    Number of Heartbeats before app manager forces a restart.
	UPREQTIMEOUT number                       30000    Timeout for obtaning Join collection mutexes for normal access/update req.
	BUILDIFOFFLINE ON|OFF                       OFF    Build/Send packet even if device is offline.
	SENDPARAMETERS ON|OFF                       OFF    Always obey SendParameters() call.
	PJG ON|OFF                                  OFF    Page Join Gating debugs.
	UPREQ ON|OFF                                OFF    Update Request debug.
	PJGTIMEOUT time                           20200    Timeout for to wait for Page Join Gating Sync event
	DMPS3 ON|OFF                                OFF    Show some DMPS3 debug info.
	ERSLEEPY                                           Show ErSleepy device information.
	DTADELAY                                    OFF    TLDM Data to App Delay debugs.
	BACNETSTOPPEDTIMEOUT                         15    Overall timeout for Bacnet to complete stop, in min.
```

### SSHPORt

**Role:** Administrator | **Description:** Enable/Disable and configure SSH port number

```
SSHPORT [OFF | ON | port number]
	[OFF | ON ] - Disables/Enables SSH. Default is ON
	portnumber - desired port number (in decimal).
	no parameter - displays current value
```

### SSHSERVer

**Role:** User | **Description:** Configure the SSH server and the public keys

```
SSHSERVer <subcommand>
	ADDUSERKEY -N:username -K:keyfilename -- Adds the public key file to an existing user account
		-N: specifies name of a local user
		-K: specifies name of a public key file pre-uploaded to \user folder
	REMUSERKEY -N:username -- Removes the public key from an existing user account
		-N: specifies name of a local user
	LISTUSERKEY -N:username -- Displays the public key from an existing user account
		-N: specifies name of a local user
	KEYEXCHANGE -A:<kex_algo_name> [on|off] -- Enables/Disables specified SSH key exchange algorithm in FIPS mode
		-A: specifies name of the algorithm
		NOTE: The only algorithm currently supported by the command is 'diffie-hellman-group-exchange-sha256' (Alias:'DHGEX256')
	HMAC -A:<hmac_algo_name> [on|off] -- Enables/Disables specified SSH HMAC algorithm in FIPS mode
		-A: specifies name of the algorithm
		NOTE: The only algorithms currently supported by the command are 'hmac-sha2-256-etm@openssh.com' (Alias:'HMACSHA2256ETM') and 'hmac-sha2-512-etm@openssh.com' (Alias:'HMACSHA2512ETM')
	SHA1 [on|off] -- Enables/Disables SHA1 algorithm
	GENHOSTKEY -- Regenerate the SSH host keys
```

### SSL

**Role:** Administrator | **Description:** Display/Set SSL type

```
SSL [SELF | CA [-P:privatekeypassword]]
	where
	  'SELF' configures SSL to use a self-signed certificate.
	  'CA' configures SSL to use a CA-signed certificate; if an
	    encrypted external private key file is used with this
	    certificate, the password may be specified with the '-P:'
	    option - otherwise, the system will prompt for a password.
	  No parameter: displays the current SSL settings.
```

### SSLVERIFY

**Role:** Administrator | **Description:** Display/Set SSL certificate verification.

```
SSLVERIFY [ALL] | [[OFF|CA] | [-T:ON|OFF]] [-X:ON|OFF] [-C:ON|OFF] [-S:ON|OFF] [-H:ON|OFF]
	'ALL' enables all verification options,
	'OFF' disables server certificate trust check (allow both SELF and CA certificates),
	'CA' ensures that a server certificate is issued by a trusted CA,
	-T:ON|OFF enable/disable verification that a server certificate is issued by a trusted CA,
	-X:ON|OFF enable/disable required presence of extendedKeyUsage in server certs,
	-C:ON|OFF enable/disable required presence of CA in basicConstraints of
	   installed server certs,
	-S:ON|OFF enable/disable required trusted signer on installed server certs,
	-H:ON|OFF enable/disable server certificate hostname checking,
	The OFF and CA parameters are deprecated; use the -T switch instead.
	The X option applies to outgoing TLS connections and to
	   installed server certificates.
	No parameter - displays current setting
```

### SSPTASKs

**Role:** Operator | **Description:** (*) Show currently executing user threads in SIMPL# Pro.

```
SSPTASKs[:program#]
	View a list of the executing user threads in a SIMPL# Pro program.
	No arguments necessary.
```

### STOPLIGHTBYPPn

**Role:** Operator | **Description:** Stop Light And Poll mode

```
Valid options are:
   Status if no arguments

Syntax: STOPLIGHTBYPPN [4 byte Hex Adr]|ALL [SHOW]
```

### STOPPROGram

**Role:** Operator | **Description:** Stops the specified program

```
STOPPROGRAM {-P:ALL | -P:Specific Program Identifier} {-V} {-K}
 	 -P:  Stop a specific program or ALL.  If not present, ALL assumed..
 	 -V:  Verbose shutdown.
 	 -K:  Keep DBGSIGNAL information (STOPPROG normally clears DBGSIGNAL flags)
```

### SUPPORTCIPSHA1Ciph

**Role:** Administrator | **Description:** Enable/Disable use of RSA-SHA1 ciphers.

```
SUPPORTCIPSHA1Ciph [<ON/OFF>]
	 Enable/Disable all SHA1 ciphers used in client/server SSL connections. 
	 ON - Enables the ciphers.
	 OFF - Disables the ciphers.
	 NONE - Shows current state of all ciphers.
	 Reboot for changes to take into effect.
```

### SUPPORTRSAAES128ciph

**Role:** Administrator | **Description:** Enable/Disable use of TLS_RSA_WITH_AES_128_CBC_SHA cipher.

```
SUPPORTRSAAES128Ciph 
	 Enable/Disable TLS_RSA_WITH_AES_128_CBC_SHA cipher for use in client/server. 
	 ON - Enables TLS_RSA_WITH_AES_128_CBC_SHA cipher.
	 OFF - Disables TLS_RSA_WITH_AES_128_CBC_SHA cipher.
	 Needs reboot for changes to take into effect.
```

### SUSERPROGCMD

**Role:** Operator | **Description:** (*) Send a command from the console to the user program

```
USERPROGCMD[:program#] {quoted string}
	program#: number of program to execute. (default=1)
	Escape sequences will be translated, quotes will not be sent to user program.
	The program needs a "User Program Commands" symbol to receive the data
```

### SYMSETSIG

**Role:** Operator | **Description:** (*) Set the state of the signal in the program

```
SYMSETSIG[:program#] symbol_number index value [A | D | S]
	program#: number of program to execute. (default=1)
	symbol number - Hex Number (i.e. 0x0000000B) or Decimal number (i.e. 11)
	                Can be gotten from ISTAT PROG | DEV | REGDEV
	index         - Hex Number (i.e. 0x0000000B) or Decimal number (i.e. 11)
	                0 based index into existing signals on symbol.
	value         - 0 or 1 for Digital
	              - pXX : Pulse XX ms long for Digital
	              - iXX : Inverse pulse XX ms long for Digital
	              - 0 to 65535 for Analog
	              - Quoted string for Strings
	[A|D|S]       - Optional List specifier for Trilisted symbols
	                (Analog, Digital, Serial).  index is then 0 based
	                into the respective list.
```

### SYSLOG

**Role:** Operator | **Description:** Enable/disable system UI log.

```
SYSLOG [ON|OFF|CLEAR|PRINT|LOGNOTICEON|LOGNOTICEOFF|LOGEXTRAON|LOGEXTRAOFF|LOGARCHIVEON|LOGARCHIVEOFF]
	 Enable/disable UI system logging.
	 No Parameters - Displays current setting
```

### SYSMON

**Role:** Operator | **Description:** System Monitor Control

```
Local commands affecting individual monitors
	xx [c|d|e|f|r|s|?] - show/flags/help specific monitors
	? - show this monitor help
	Calibrate - reset idle system load factor
	Disable|OFF - stop monitoring this option
	Enable|ON  - start monitoring this option
	Flags [#dec value] - set specific flags to value
	Reset - reset min/max stats for this monitor
	Show run-time - toggle run-time display for this monitor
Example:
 3 show on - will set run-time display option to ON
Global commands affecting all
  Disable|OFF - disable globally
  Enable|ON - enable globally
  Id stats - show cresnet stats by ID
  Minmax - show minimum/maximum stats for all
  Reset  - reset min/max stats
  Save  - save settings
  Timing xx - update loop in seconds
```

### SYSTEMREADY

**Role:** Programmer | **Description:** Display the system ready status

```
SystemReady: True
```

### TASKSTAT

**Role:** Operator | **Description:** Lists applications in system

```
TASKSTAT
	Usage:
	  taskstat
	  taskstat                - list processes with cpu & memory usage
	  taskstat -pss           - list processes with pss memory usage
	  taskstat -t             - list processes, threads with cpu & memory usage
	  taskstat -find:text     - list processes, threads filtered
lists application in system.
```

### TCPKEEPALIVE

**Role:** Programmer | **Description:** Enable/disable TCP Keep Alive

```
TCPKeepAlive [ON | OFF] 
	Enables/Disables TCP Keep Alive 
	TCP Keep Alive is supported for Client-Servers / Direct Socket  Client-Servers / Console connections 
	No parameter - displays current setting
```

### TEMPTest

**Role:** Operator | **Description:** Board Temperature test.

```
Usage: TEMPTest [-s]|[-k] [--i=]
	-s:				start a Temperature-Test session
	-k:				kill/stop the Temperature-Test session currently running
	--i=<interval>:				Interval for temp request in loop.
```

### TESTDNS

**Role:** Operator | **Description:** Test DNS Server

```
TESTDNS string
	string - ASCII string containing host name
```

### TESTLOGIn

**Role:** Administrator | **Description:** Test authentication and authorization

```
TESTLOGIN username [-P:password] [-I:source_ip]
  -P: specifies the password for the user
  Prompts for password if not specified.
  -I: specifies a login source IP
  The login source IP is for testing purposes only and is not validated.
  'username' may be of the form:
    <domain>\<user>
    <user>@<domain>
    <user>
```

### TESTLOGOut

**Role:** Administrator | **Description:** Test logout for login via TESTLOGIN

```
TESTLOGOUT username
  Performs logout actions for a user logged in via TESTLOGIN
  'username' may be of the form:
    <domain>\<user>
    <user>@<domain>
    <user>
```

### TESTWATCH

**Role:** Operator | **Description:** Test watchdog timer

```
TESTWATCH [HW | SW]
	HW - test the hardware watchdog timer
	SW - test the software watchdog timer
```

### THREADPOOLINFO

**Role:** Operator | **Description:** (*) Information about the Custom App Thread pool.

```
THREADPOOLINFO[:program#]
	View Thread Pool Information.
	No arguments necessary.
```

### TIMEREVENTMAXQueuesize

**Role:** Administrator | **Description:** Set queue size to hold maximum timer events

```
TIMEREVENTMAXQUEUESIZE [queueSize]
	 queueSize - Queue size to accommodate maximum timer events
	 no parameter - Displays current value
```

### TIMEZone

**Role:** Administrator | **Description:** Get/Set the timezone

```
TIMEZONE [LIST | zone]
	LIST - print timezones
	zone - number of the timezone to set
	No parameter - displays current setting
```

### TIMEdate

**Role:** Programmer | **Description:** Get the time and date

```
TIMEdate [hh:mm:ss mm-dd-yyyy]
	hh:mm:ss - time in hours (use 24hr), mins and secs
	mm/dd/yyyy or mm-dd-yyyy - date in months(1-12), day(1-31) and year
	No parameter - displays current setting
```

### TLS13CIPHER

**Role:** Administrator | **Description:** Set/Get the class of ciphers/algorithms used for TLS 1.3 encryption

```
TLS13CIPHER [REDUCED/ALL]
	ALL - Enables all of the ciphers/algorithms for use for TLS1.3 encryption
	REDUCED - Disables TLS_CHACHA20_POLY1305_SHA256, X25519, ed25519, and ed448 for use for TLS1.3 encryption
	No parameter - displays current value
```

### TLSCIPHER

**Role:** Administrator | **Description:** Set/Get the class of ciphers/algorithms used for TLS 1.2 encryption

```
TLSCIPHER [STRONG/COMPATIBILITY/NOSHA1/AESCIPHERS]
	parameter - desired set of ciphers/algorithms the device will use for TLS encryption
	parameter - Ciphers may also be affected by the SUPPORTCIPSHA1CIPH, SUPPORTRSAAES128CIPH, and TLS13CIPHER commands.
	No parameter - displays current value
```

### TLSVERsion

**Role:** Administrator | **Description:** Set the minimum TLS version.

```
TLSVERSION [TLS1.2|TLS1.3|BOTH]
	where 'TLS1.2' indicates that this is the required version for TLS connections.
	where 'TLS1.3' indicates that this is the required version for TLS connections.
	where 'BOTH' indicates that both TLS1.2 and TLS1.3 are OK for TLS connections.
	No parameter - displays the current setting
```

### TOP

**Role:** Operator | **Description:** Lists proceseses and threads in system

```
TOP usage:
	  lists processes and threads in system with cpu & memory usage
	  top [-find:text] [-lines:#|ALL] [-col:#] [-sort:] [-rsort:sort options]  [-p:##|ALL]
	     -t        show threads, only with single columns
	     -p        filter crestron apps [##] or [ALL]
	     -lines    number of lines to display, default 25, all|ALL for all lines
	     -col      number of columns to display, default 1
	     -find     case insensitive filter, words can be quoted
	     -sort     ascending sort (default pid)
	     -rsort    desending sort
	        sort options: pid, cpu, time, mem, name, thread
	  example: top -col:2
	  example: top -t -lines:40 -col:2 -rsort:mem
	  example: top -find:ctpd -lines:ALL -rsort:mem
	  example: top -t -p:1
	  example: top -p:ALL
```

### TRACEROUTE

**Role:** Administrator | **Description:** Trace the route of an IP address

```
TRACEROUTE <address>
	address - address to trace
```

### TRIGGEREVents

**Role:** Programmer | **Description:** Trigger timer events for application id.

```
Trigger timer event for specified event group within program id. 
TRIGGEREVENTS -I:ProgramTag -G:GroupEventName -E:EventName 
	 -I: ProgramTag/UserDefinedTag 
	 -G: Group Event Name
	 -E: Event Name
```

### TYPE

**Role:** Operator | **Description:** Display file contents

```
TYPE filename
	filename - the name of the file to display
```

### UCMD

**Role:** Operator | **Description:** (*) Send a command from the console to the user program

*No detailed help available.*

### UPDATEPassword

**Role:** User | **Description:** Update current local user's password

*No detailed help available.*

### UPGRADERESULTS

**Role:** Operator | **Description:** Print results of last upgrade command

*No detailed help available.*

### UPLOAD

**Role:** Programmer | **Description:** Load file into cresnet device

*No detailed help available.*

### UPTIME

**Role:** Operator | **Description:** Display the time the system is running

*No detailed help available.*

### USERInformation

**Role:** Administrator | **Description:** Show access information for a specific user

*No detailed help available.*

### USERPAGEAUTH

**Role:** Administrator | **Description:** User page Authentication on/off

*No detailed help available.*

### USERPAGETokenauth

**Role:** Administrator | **Description:** User page Token Authentication on/off

*No detailed help available.*

### USERPROGCMD

**Role:** Operator | **Description:** (*) Send a command from the console to the user program

```
USERPROGCMD[:program#] {quoted string}
	program#: number of program to execute. (default=1)
	Escape sequences will be translated, quotes will not be sent to user program.
	The program needs a "User Program Commands" symbol to receive the data
```

### VALIDATEAUTHDOMain

**Role:** Administrator | **Description:** Validate authentication domain configuration

```
UPDATEPASSWORD
 	No parameters needed
```

### VERsion

**Role:** Operator | **Description:** Print version to console

```
UPGRADERESULT - show result of last upgrade
```

### WAVEDUMP

**Role:** Operator | **Description:** (*) Dump Logic Wave Information

```
Valid options are:
 CRESnet -  UPLOAD Over Cresnet
 SLOT - plug-in card
 UPLOad - device upgrade
 CODE - device upgrade
 FIrmware - device upgrade
 DATA - xmodem xfer mode
 SCreen - xmodem xfer mode
    hex number allowed as argument
 UPLOAD [SLOT|CRESnet(default)] ID_OR_SLOT_NUM [FIRMWARE |CODE | SCREEN |DATA(default)]
```

### WBALLOW

**Role:** Operator | **Description:** (*) wballow

```
UPTIME 
	no parameters needed
```

### WBBTN

**Role:** Operator | **Description:** (*) wbbtn

```
USERINFOrmation username
	 username - Show the access information of the specified user.
```

### WBDELETEPAIRING

**Role:** Operator | **Description:** (*) wbdeletepairing

```
USERPAGEAUTH [OFF | ON]
	ON - turns on User Page Authentication.
	OFF - turns off User Page Authentication.
	No parameter - displays current setting
```

### WBINIT

**Role:** Operator | **Description:** (*) wpinitt

```
USERPAGETOKENAUTH [OFF | ON]
	ON - turns on User Page Token Authentication.
	OFF - turns off User Page Token Authentication.
	No parameter - displays current setting
```

### WBIP

**Role:** Operator | **Description:** (*) wpip

```
USERPROGCMD[:program#] {quoted string}
	program#: number of program to execute. (default=1)
	Escape sequences will be translated, quotes will not be sent to user program.
	The program needs a "User Program Commands" symbol to receive the data
```

### WBJOIN

**Role:** Operator | **Description:** (*) wbjoin

```
VALIDATEAUTHDOMAIN domain_name
    domain_name - specifies the name of the authentication domain to validate
  Depending on the domain type, validation may require network connectivity
```

### WBLEAVE

**Role:** Operator | **Description:** (*) wbleave

```
VERSION [-v]
	-v : show extended version info
```

### WBPAIR

**Role:** Operator | **Description:** (*) wppair

```
WAVEDUMP[:program#] arguments

	program#: number of program to execute. (default=1)
	Set parameters/display the Logic Wave history.
	-C:ON|OFF  Dump list of last symbols executed after a
	           "Could not solve logic within %d waves." error to Console.

	-F:ON|OFF  Dump list of last symbols executed after a
	           "Could not solve logic within %d waves." error to File.
	-S:#       Store information for up to this number of symbols
	-L         Dump the wavelist.

	Note:  Wave Dumps may not show a full history for a solution depending on the size of the wave history.
	       When using this command it is highly recommended to use the -C:ON and/or -F:ON form to dump the list immediately, not -L.
```

### WBSHOW

**Role:** Operator | **Description:** (*) wpshow

*No detailed help available.*

### WBSTART

**Role:** Operator | **Description:** (*) wbstart

*No detailed help available.*

### WBSTOP

**Role:** Operator | **Description:** (*) wbstop

*No detailed help available.*

### WBSTOPWITHSNAPSHOT

**Role:** Operator | **Description:** (*) wbstopwithsnapshot

*No detailed help available.*

### WBSTOPWITHTIMELINE

**Role:** Operator | **Description:** (*) wbstopwithtimeline

*No detailed help available.*

### WBUNPAIR

**Role:** Operator | **Description:** (*) wpunpair

*No detailed help available.*

### WEBINIT

**Role:** Programmer | **Description:** Initialize Webserver default file.

```
WEBINIT 
no parameters needed
```

### WEBPORT

**Role:** Administrator | **Description:** Set port number for Webserver.

```
WEBPORT [portnumber]
	portnumber - desired port number (in decimal).
	No parameter - displays the current value
```

### WEBSERVER

**Role:** Administrator | **Description:** Enable/disable Webserver

```
WEBSERVER [ON | OFF | TIMEOUT <VALUE IN SECONDS> | MAXSESSIONSPERUSER <Number of sessions> | TOTALUSERSESSIONS <Number of sessions> | ADAPTER <ADAPTERNAME | LIST | ALL> | MGMT <ON [PORT]| OFF> ] 
WEBSERVER [TIMEOUT] will display current session timeout value
WEBSERVER MAXSESSIONSPERUSER will display current max web sessions per user
WEBSERVER TOTALUSERSESSIONS will display current total web sessions for users
WEBSERVER ALLOWSHAREDSESSION will display whether 'samesite = none' would be set on cookies
WEBSERVER ADAPTER will display current adapter/interface used 
WEBSERVER ADAPTER <LIST> will display available adapters/interfaces
WEBSERVER MGMT will display current management port used
WEBSERVER SHA1 will display if webserver supports ciphers with SHA1 algorithm
WEBSERVER Referrer-policy to set the Referrer-Policy in response headers
WEBSERVER cachecontrol to set the Cache-Control value in response headers
WEBSERVER compression to enable/disable setting Conent-Encoding response header
	No parameter - displays current setting
```

### WEBSOCKETTOKEN

**Role:** Administrator | **Description:** Manage JWT authorization token

```
WEBSOCKETTOKEN 	[DELETE | GENERATE] 
DELETE - Deletes the existing authorization token
GENERATE - Generate new authorization token if not yet created
No Parameter - Display current authorization if already created
```

### WHO

**Role:** Administrator | **Description:** Generate a report of the Ethernet consoles

```
WHO
	 No Parameter necessary
```

### WHOAmi

**Role:** Operator | **Description:** Display current user's identity

```
WHOAMI
	No parameter needed.
```

### XGETfile

**Role:** Operator | **Description:** Use XMODEM to transfer file from ROM

```
XGET filename
	filename - name of the file
```

### XPUTfile

**Role:** Operator | **Description:** Use XMODEM to transfer file to ROM

```
XPUT size date time name
	size - size of the file in bytes
	date - date of the file (MM-DD-YY)
	time - UTC time of the file (HH:MM:SS)
	name - name of the file
```
