#!/usr/bin/env python

from machinekit import hal, rtapi
import logging
import signal


class DIOTestSetup:

    thread_name = 'test_thread'
    thread_freq = 1000000  # 1ms
    test_comp_name = 'dio_test'
    dio_module_pin_prefix = 'lcec.0.6'  # $PREFIX.d{in,out}-{0..15}
    num_pins = 16
    logger = logging.getLogger('test_setup')

    def __init__(
        self,
        lcec_config_file='./ethercat-za6.xml',
        test_comp='./dio_test_comp.py',
    ):
        self.logger.debug('LCEC config file:  %s' % lcec_config_file)
        self.lcec_config_file = lcec_config_file
        self.logger.debug('Test comp:  %s' % test_comp)
        self.test_comp = test_comp

    def out_pin_names(self, i):
        return (
            '{}.out{}'.format(self.test_comp_name, i+1),
            '{}.dout-{}'.format(self.dio_module_pin_prefix, i),
        )

    def in_pin_names(self, i):
        return (
            '{}.in{}'.format(self.test_comp_name, i+1),
            '{}.din-{}'.format(self.dio_module_pin_prefix, i),
        )

    def setup(self):
        # Init RTAPI
        self.logger.debug('Starting HAL')
        rtapi.init_RTAPI()

        # Load EtherCAT comp, add to thread, start
        self.logger.debug('Loading LCEC component')
        hal.loadusr(
            "lcec_conf %s" % self.lcec_config_file, wait=True, wait_timeout=10.0
        )
        rtapi.loadrt("lcec")
        rtapi.newthread(self.thread_name, 1000000, fp=True)
        hal.addf('lcec.0.read', self.thread_name)
        hal.addf('lcec.0.write', self.thread_name)
        hal.start_threads()

        # Load DIO test comp
        self.logger.debug('Loading dio_test component')
        hal.loadusr(self.test_comp, wait=True, wait_name=self.test_comp_name)

        # Net pins
        for i in range(self.num_pins):
            # input pin
            sig_name = 'in%s' % i
            sig = hal.newsig(sig_name, hal.HAL_BIT)
            for pin_name in self.in_pin_names(i):
                self.logger.debug('Netting sig {} to {}'.format(sig_name, pin_name))
                sig.link(pin_name)
            # output pin
            sig_name = 'out%s' % i
            sig = hal.newsig(sig_name, hal.HAL_BIT)
            for pin_name in self.out_pin_names(i):
                self.logger.debug('Netting sig {} to {}'.format(sig_name, pin_name))
                sig.link(pin_name)
        self.logger.info('Test setup complete')

    def spin(self):
        signal.pause()
        self.logger.info('Exiting test setup')


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
    test = DIOTestSetup()
    test.setup()
    test.spin()
