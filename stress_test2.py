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
    
#CTestNetParams
nPowTargetSpacing = 1 * 60

#node1 should be a masternode started with "-govtest" parameter
node1 = DashDaemon(host = '127.0.0.1', user='user', password = '1', port = '20101')
#node2 and node3 are regular masternodes
node2 = DashDaemon(host = '127.0.0.1', user='user', password = '1', port = '20002')
node3 = DashDaemon(host = '127.0.0.1', user='user', password = '1', port = '20003')

#log1 = testtools.LogListener('/tmp/node101', 10)
#log2 = testtools.LogListener('/tmp/node2', 10)
#log3 = testtools.LogListener('/tmp/node3', 10)

nSuperblockCycleSeconds = node1.superblockcycle() * nPowTargetSpacing

while(not node1.is_synced() or not node2.is_synced() or not node3.is_synced()):
    print('not yet synced, sleep 30 sec')
    time.sleep(30)
   

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
    end_epoch=end_epoch,
    govobj_type=0
)


print proposal.govobj_type
proposal.govobj_type = 0

#cmd = ['gobject', 'submit', '0', '1', str(curunixtime), proposal.dashd_serialise(), '0463c5b7194605e598441422a3dc99c7c96df4c943dd047310646ae2d8c43add']
cmd = ['gobject', 'submit', '0', '1', str(curunixtime), proposal.dashd_serialise(), '0000000000000000000000000000000000000000000000000000000000000000']

count = 0
while True:
    try:
        object_hash = node1.rpc_command(*cmd)
    except:
        time.sleep(1)
        continue

    print 'submit invalid proposal #{0}: {1}'.format(count, object_hash)
    count += 1
    curunixtime += 1
    cmd[4] = str(curunixtime)

#log1.close()
#log2.close()
#log3.close()
