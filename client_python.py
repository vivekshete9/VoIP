import sys
import pjsua as pj#Importing pjsip 2.0.1

LOG_LEVEL=3
curr_call = None

def log_callback(level, str, len):
    print str,

# Callback to receive events from account
class MyAccountCallback(pj.AccountCallback):
    sem= None

    def init(self, account=None):
        pj.AccountCallback.init(self, account)

    def on_reg_state(self):
        if self.sem:
            if self.account.info().reg_status >= 200:
                self.sem.release()

    # Notify on incoming call
    def incoming_call(self, call):
        global curr_call 
        if curr_call:
            call.answer(486, "Busy")
            return
            
        print "Incoming call from ", call.info().remote_uri
        print "Type 1 to answer"

        curr_call = call

        call_cb = MyCallCallback(curr_call)
        curr_call.set_callback(call_cb)

	#for ringing
        curr_call.answer(180)

        
# Callback to receive events from Call
class MyCallCallback(pj.CallCallback):

    def init(self, call=None):
        pj.CallCallback.init(self, call)

    # Notify when call state has changed
    def on_state(self):
        global curr_call
        print "Call with", self.call.info().remote_uri,
        print "is", self.call.info().state_text,
        print "last code =", self.call.info().last_code, 
        print "(" + self.call.info().last_reason + ")"
 

    # Notify when call's media state has changed.
    def on_media_state(self):
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            # Connect the call to sound device
            call_slot = self.call.info().conf_slot
            pj.Lib.instance().conf_connect(call_slot, 0)
            pj.Lib.instance().conf_connect(0, call_slot)
            
        else:
            print "Media is not active"

# Function to make call
def make_call(uri):
    try:
        print "Making call to", uri
        return acc.make_call(uri, cb=MyCallCallback())
    except pj.Error, e:
        print "Exception: " + str(e)
        return None
        

# Create library instance
lib = pj.Lib()

try:
    # Initialize library
    lib.init(log_cfg = pj.LogConfig(level=LOG_LEVEL, callback=log_callback))

    # Configuring one Transport Object
    tran_conf = pj.TransportConfig()
    tran_conf.bound_addr = "192.168.100.50"     # IP address of PJSIP client
    transport = lib.create_transport(pj.TransportType.UDP, 
pj.TransportConfig(0))                            
    print "\nListening on", transport.info().host, "\n"

    # Start library
    lib.start()

    # Configuring Account class to register with Registrar server
    acc_conf = pj.AccountConfig(domain = '192.168.100.50', username = '2050', password = 'password', display = '2050', registrar = 'sip:192.168.100.1', proxy = 'sip:192.168.100.1')
    acc_conf.id = "sip:2050"
    acc_conf.reg_uri = "sip:192.168.100.1"

    # Creating account
    acc = lib.create_account(acc_conf)
    cb = MyAccountCallback(acc)
    acc.set_callback(cb)

    if len(sys.argv) > 1:
        lck = lib.auto_lock()
        curr_call = make_call(sys.argv[1])
        print 'Current call is', curr_call
        del lck

    SipUri_mine = "sip:" + transport.info().host + \
                 ":" + str(transport.info().port)

    # Menu 
    while True:
        print "My own SIP URI: ", SipUri_mine
        print "\nPress:\n1 to answer\n2 to hangup\n3 to make call\n4 to quit\n"
        input = sys.stdin.readline().rstrip("\r\n")
        if input == '3':
            if curr_call:
                print "Currently in another call"
                continue
            print "Enter destination URI to call in the syntax ", 
            input = sys.stdin.readline().rstrip("\r\n")
            if input == "":
                continue
            lck = lib.auto_lock()
            curr_call = make_call(input)
            del lck

        elif input == '2':
            if not curr_call:
                print "There is no call"
                continue
            curr_call.hangup()

        elif input == '1':
            if not curr_call:
                print "There is no call"
                continue
            curr_call.answer(200)

        elif input == '4':
	    print "Shutting down"
            break

    # Shutdown the library
    transport = None
    acc.delete()
    acc = None
    lib.destroy()
    lib = None

except pj.Error, e:
    print "Exception: " + str(e)
    lib.destroy()
lib = None
