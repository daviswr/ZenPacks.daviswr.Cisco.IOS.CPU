__doc__ = """CiscoCpuMap

maps SNMP processor information onto CPU components

"""

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs


class CiscoCpuMap(SnmpPlugin):
    maptype = 'CPUMap'
    compname = 'hw'
    relname = 'cpus'
    modname = 'Products.ZenModel.CPU'

    cpmCPUTotalEntry = {
        '.2': 'cpmCPUTotalPhysicalIndex',
        }

    entPhysicalEntry = {
        '.2': 'entPhysicalDescr',
        '.4': 'entPhysicalContainedIn',
        '.7': 'entPhysicalName',
        '.12': 'entPhysicalMfgName',
        '.13': 'entPhysicalModelName',
        }

    snmpGetTableMaps = (
        GetTableMap(
            'cpmCPUTotalTable',
            '.1.3.6.1.4.1.9.9.109.1.1.1.1',
            cpmCPUTotalEntry
            ),
        GetTableMap(
            'entPhysicalTable',
            '.1.3.6.1.2.1.47.1.1.1.1',
            entPhysicalEntry
            ),
        )

    def condition(self, device, log):
        """determine if this modeler should run"""
        # CISCO-SMI::ciscoProducts
        if not device.snmpOid.startswith('.1.3.6.1.4.1.9.1'):
            log.info('%s is not a Cisco IOS device', device.id)
        return device.snmpOid.startswith('.1.3.6.1.4.1.9.1')

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        getdata, tabledata = results

        cpuTable = tabledata.get('cpmCPUTotalTable')
        if cpuTable is None:
            log.error('Unable to get cpmCPUTotalTable for %s' % device.id)
            return None
        else:
            log.debug(
                'cpmCPUTotalTable has % entries',
                len(cpuTable)
                )

        entTable = tabledata.get('entPhysicalTable')
        if entTable is None:
            log.error('Unable to get entPhysicalTable for %s' % device.id)
            return None
        else:
            log.debug(
                'entPhysicalTable has %s entries',
                len(entTable)
                )

        # Processors
        rm = self.relMap()

        for snmpindex, row in cpuTable.items():
            if not rm and not self.checkColumns(row, self.columns, log):
                return rm
            om = self.objectMap()
            om.snmpindex = snmpindex.strip('.')

            # Many fixed-config switches and small routers return 0 for
            # cpmCPUTotalPhysicalIndex and have no entPhysicalName.0 object,
            # but have entPhysicalName.1. The Catalyst 3560 is a notable
            # exception, starting with entPhysicalName.1001.
            entIndex = str(row.get('cpmCPUTotalPhysicalIndex', None))
            if entIndex not in entTable:
                log.debug(
                    'Index %s not found in entPhysicalTable, using %s',
                    entIndex,
                    snmpindex
                    )
                entIndex = str(snmpindex)
                if entIndex not in entTable:
                    entIndex = str(1000 + int(entIndex))
                    log.debug(
                        'Index %s not found in entPhysicalTable, using %s',
                        snmpindex,
                        entIndex
                        )

            entity = entTable.get(entIndex, dict())
            model = entity.get('entPhysicalModelName', None)
            if model is None or len(model) == 0:
                log.debug('entPhysicalModelName not available')
                model = entity.get('entPhysicalDescr', None)
                if model is None or len(model) == 0:
                    log.debug('entPhysicalDescr not available')
                    model = entity.get('entPhysicalName', None)
                    if model is None or len(model) == 0:
                        log.debug('entPhysicalName not available')
                        model = 'CPU {0}'.format(om.snmpindex)

            if model.lower().find('cpu') < 0 or model.lower().find('proc') < 0:
                model = 'CPU of {0}'.format(model)

            mfg = entTable[entIndex].get('entPhysicalMfgName')
            if mfg is None or len(mfg) == 0:
                log.debug('entPhysicalMfgName not available')
                mfg = 'Cisco'

            socket = entTable[entIndex].get('entPhysicalContainedIn')
            if socket is None or len(str(socket)) == 0:
                log.debug('entPhysicalContainedIn not available, using 0')
                socket = '0'
                # TODO: Set socket value in ObjectMap

            log.debug(
                'Index: %s, Model: %s, Manufacturer: %s',
                entIndex,
                model,
                mfg
                )
            om.setProductKey = MultiArgs(model, mfg)
            om.id = self.prepId(model)
            rm.append(om)

        log.debug('%s RelMap:\n%s', self.name(), str(rm))
        return rm
