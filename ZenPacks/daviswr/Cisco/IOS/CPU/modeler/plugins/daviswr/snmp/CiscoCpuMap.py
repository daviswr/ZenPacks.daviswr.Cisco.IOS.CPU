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
        '.2':'entPhysicalDescr',
        '.7':'entPhysicalName',
        '.12':'entPhysicalMfgName',
    }

    snmpGetTableMaps = (
        GetTableMap('cpmCPUTotalTable', '.1.3.6.1.4.1.9.9.109.1.1.1.1', cpmCPUTotalEntry),
        GetTableMap('entPhysicalTable', '.1.3.6.1.2.1.47.1.1.1.1', entPhysicalEntry),
    )

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        getdata, tabledata = results
        cpuTable = tabledata.get('cpmCPUTotalTable')
        if cpuTable is None:
            log.error('Unable to get data for %s for cpmCPUTotslTable -- skipping model' % device.id)
            return None
        entTable = tabledata.get('entPhysicalTable')
        if entTable is None:
            log.error('Unable to get data for %s for entPhysicalTable -- skipping model' % device.id)
            return None
        rm = self.relMap()
        #for entity in entTable.items():
        #    log.debug('Entity %s - %s' % (entity[0], entity[1]))
        for snmpindex, row in cpuTable.items():
            if not rm and not self.checkColumns(row, self.columns, log): 
                return rm
            om = self.objectMap()
            om.snmpindex = snmpindex.strip('.')

            # Many fixed-config switches and small routers return 0
            # for cpmCPUTotalPhysicalIndex and have no entPhysicalName.0 object,
            # but have entPhysicalName.1. The Catalyst 3560 is a notable exception,
            # starting with entPhysicalName.1001.
            entIndex = str(row['cpmCPUTotalPhysicalIndex'])
            if not entIndex in entTable:
                log.debug('Index %s not found in entPhysicalTable, using index %s' % (entIndex, snmpindex))
                entIndex = str(snmpindex)
                if not entIndex in entTable:
                    entIndex = str(1000 + int(entIndex))
                    log.debug('Index %s not found in Entity table, using index %s' % (snmpindex, entIndex))
            model = entTable[entIndex].get('entPhysicalModelName')
            if model is None or len(model) == 0:
                log.debug('entPhysicalModelName not available, using entPhysicalName')
                model = entTable[entIndex].get('entPhysicalName')
                if model is None or len(model) == 0:
                    log.debug('entPhysicalName not available, using entPhysicalDescr')
                    model = entTable[entIndex].get('entPhysicalDescr')
                    if model is None or len(model) == 0:
                      log.debug('entPhysicalDescr not available, using default model')
                      model = 'CPU {}'.format(str(om.snmpindex))
            mfg = entTable[entIndex].get('entPhysicalMfgName')
            if mfg is None or len(mfg) == 0:
                log.debug('entPhysicalMfgName not available, using default manufacturer')
                mfg = 'Cisco'
            log.debug('Index: %s, Model: %s, Manufacturer: %s' % (entIndex, model, mfg))
            om.setProductKey = MultiArgs(model, mfg)
            om.id = self.prepId(model)
            rm.append(om)

        return rm
