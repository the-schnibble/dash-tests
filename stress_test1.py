#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sudo apt install python-pip
# sudo pip install python-bitcoinrpc simplejson sortedcontainers

import time
import testtools
from models import Superblock
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
   

# create trigger

event_block_height = node1.next_superblock_height()
payment_amounts = 5

sbobj = Superblock(
	event_block_height=event_block_height,
	payment_addresses='yYe8KwyaUu5YswSYmB3q3ryx8XTUu9y7Ui',
	payment_amounts='{0}'.format(payment_amounts),
	proposal_hashes='e8a0057914a2e1964ae8a945c4723491caae2077a90a00a2aabee22b40081a87',
)

sb_time = int(now())
cmd = ['gobject', 'submit', '0', '1', str(sb_time), sbobj.dashd_serialise()]

#log1.expect_minimum('push_inventory:govobj {0}'.format(object_hash), 1)
#log2.expect_minimum('missing_mn:govobj {0}'.format(object_hash), 1, 0)
#log3.expect_minimum('missing_mn:govobj {0}'.format(object_hash), 1, 0)

curtime = now()
sb_time = int(curtime - 2*nSuperblockCycleSeconds + 1)

count = 0
while True:
    try:
        object_hash = node1.rpc_command(*cmd)
    except:
        time.sleep(1)
        continue

    print 'submit trigger #{0} with dummy MN: {1}'.format(count, object_hash)
    count += 1
    sb_time += 1
    if (sb_time >= curtime + 3600):
        curtime = now()
        sb_time = int(curtime - 2*nSuperblockCycleSeconds + 1)
        sbobj.event_block_height += 1
        cmd[5] = sbobj.dashd_serialise()

    cmd[4] = str(sb_time)

#log3.expect_minimum('too_many_orphans:{0}'.format(object_hash), 1, 0)

#log1.close()
#log2.close()
#log3.close()
