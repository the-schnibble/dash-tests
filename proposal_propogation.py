#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sudo apt install python-pip
# sudo pip install python-bitcoinrpc simplejson sortedcontainers

import time
import testtools
from models import Proposal
from dashd import DashDaemon

def now():
    return int(time.time())
    
def get_confirmations(dashd, txid):
    try:
        r = dashd.rpc_command("getrawtransaction", txid, 1)
    except:
        return 0
    if r.get('confirmations') is None:
        return 0
    return int(r.get('confirmations'))
        
def wait_confirmations(dashd, loglistener, txid, count):
    while True:
        confirmations = get_confirmations(dashd, txid)
        if confirmations >= count:
            break

        block_height = int(node1.rpc_command("getblockcount")) + count - confirmations
        #generate required number of blocks
        dashd.rpc_command('generate', count - confirmations)
        loglistener.expect('update_block_tip:{0}'.format(block_height), 1, 600)


#node1 should be a node started with "-govtest" parameter
node1 = DashDaemon(host = '127.0.0.1', user='user', password = 'pass', port = '30010')
#node2 and node3 are regular nodes
node2 = DashDaemon(host = '127.0.0.1', user='user', password = 'pass', port = '30008')
node3 = DashDaemon(host = '127.0.0.1', user='user', password = 'pass', port = '30009')

log1 = testtools.LogListener('/tmp/node10', 10)
log2 = testtools.LogListener('/tmp/node8', 10)
log3 = testtools.LogListener('/tmp/node9', 10)

while(not node1.is_synced() or not node2.is_synced() or not node3.is_synced()):
    print('not yet synced, sleep 5 sec')
    time.sleep(5)

# create proposal

payout_amount = 0.2
payout_month = 50

curunixtime = now()
payout_address = node1.rpc_command("getnewaddress")
proposalfee = node1.proposalfee()
superblockcycle = node1.superblockcycle()
nextsuperblock = node1.next_superblock_height()
curblock = node1.last_superblock_height()

if nextsuperblock - curblock > 10:
    start_epoch = curunixtime
else:
    start_epoch = int(curunixtime + (superblockcycle * 2.6 * 60))

end_epoch = int(start_epoch + payout_month * (superblockcycle * 2.6 * 60) + ((superblockcycle/2) * 2.6 * 60) )

proposal = Proposal(
    name='proposal_'+str(curblock),
    url='https://dashcentral.com/proposal_' +str(curblock) + '_' + str(curunixtime),
    payment_address=payout_address,
    payment_amount=payout_amount,
    start_epoch=start_epoch,
    end_epoch=end_epoch
)

print '\ntry to submit proposal with 0 confirmations'
# should be permanently rejected by all nodes

tx_hash0 = node1.rpc_command(*proposal.get_prepare_command())
print 'collateral tx hash: {0}\n'.format(tx_hash0)
log1.expect_minimum('push_inventory:tx {0}'.format(tx_hash0), 1)
cmd = ['gobject', 'submit', '0', '1', str(curunixtime), proposal.dashd_serialise(), tx_hash0]

#try to submit by regular node
try:
    node2.rpc_command(*cmd)
except:
    pass
else:
    if get_confirmations(node2, tx_hash0) < 1:
        assert False, "TEST FAILED: proposal submitted with zero confirmations"

#submit by special test node
object_hash0 = node1.rpc_command(*cmd)
print '\nproposal hash: {0}\n'.format(object_hash0)

log1.expect_minimum('push_inventory:govobj {0}'.format(object_hash0), 1)
log2.expect('govobj_received:{0}'.format(object_hash0), 1)
log3.expect('govobj_received:{0}'.format(object_hash0), 1)

if get_confirmations(node2, tx_hash0) < 1 and get_confirmations(node3, tx_hash0) < 1:
    log2.expect('govobj_accepted:{0}'.format(object_hash0), 0, 10)
    log3.expect('govobj_accepted:{0}'.format(object_hash0), 0, 0)
    log2.expect('govobj_missing_confs:{0}'.format(object_hash0), 0, 10)
    log3.expect('govobj_missing_confs:{0}'.format(object_hash0), 0, 0)

print '\ncreate new proposal'

curunixtime = now()
proposal.name = 'proposal_'+str(curblock+1)
proposal.url = 'https://dashcentral.com/' + proposal.name + '_' + str(curunixtime)

tx_hash = node2.rpc_command(*proposal.get_prepare_command())
print 'new collateral tx hash: {0}\n'.format(tx_hash)
log2.expect_minimum('push_inventory:tx {0}'.format(tx_hash), 1)

print '\nwaiting for 1 confirmation\n'
wait_confirmations(node2, log2, tx_hash, 1)

print '\nsubmit proposal with 1 confirmation'
# should be pre-accepted by node3 and automatically rebroadcasted when 6 confirmations have passed and then accepted by all nodes

cmd = ['gobject', 'submit', '0', '1', str(curunixtime), proposal.dashd_serialise(), tx_hash]
object_hash = node2.rpc_command(*cmd)
print 'new proposal hash: {0}\n'.format(object_hash)

log2.expect_minimum('push_inventory:govobj {0}'.format(object_hash), 1)
log3.expect('govobj_missing_confs:{0}'.format(object_hash), 1)
log2.expect('govobj_accepted:{0}'.format(object_hash), 0, 10)
log3.expect('govobj_accepted:{0}'.format(object_hash), 0, 0)
log3.expect('push_inventory:govobj {0}'.format(object_hash), 0, 0)

print '\nwaiting for 6 confirmations\n'
wait_confirmations(node1, log1, tx_hash, 6)

log2.expect('govobj_accepted:{0}'.format(object_hash), 1, 10)
log3.expect('govobj_accepted:{0}'.format(object_hash), 1, 0)
log2.expect_minimum('push_inventory:govobj {0}'.format(object_hash), 1, 10)
log3.expect_minimum('push_inventory:govobj {0}'.format(object_hash), 1, 0)

#check that first object has permanently rejected
#log2.expect('govobj_received:{0}'.format(object_hash0), 1)
#log2.expect('govobj_accepted:{0}'.format(object_hash0), 0, 0)
#log3.expect('govobj_received:{0}'.format(object_hash0), 1)
#log3.expect('govobj_accepted:{0}'.format(object_hash0), 0, 0)

print '\ncheck for errors\n'

assert log2.starts_with_count("inv_dropped") == 0
assert log2.starts_with_count("govobj_invalid_time") == 0
assert log2.starts_with_count("govobj_unrequested_received") == 0
assert log2.starts_with_count("govobj_seen_received") == 0
assert log2.starts_with_count("postponed_unknown_relay") == 0

assert log3.starts_with_count("inv_dropped") == 0
assert log3.starts_with_count("govobj_invalid_time") == 0
assert log3.starts_with_count("govobj_unrequested_received") == 0
assert log3.starts_with_count("govobj_seen_received") == 0
assert log3.starts_with_count("postponed_unknown_relay") == 0


print 'TEST SUCCEEDED'

log1.close()
log2.close()
log3.close()
