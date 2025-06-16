#!/usr/bin/env python

import hal
import time
import logging
import sys


class DIOTestComp:

    coalescence_period = 0.01  # enough time for input to register output change
    blink_period = 0.5  # seconds/cycle
    num_dios = 16  # input + output pairs
    comp_name = 'dio_test'
    logger = logging.getLogger(comp_name)

    @property
    def pin_range(self):
        return set(range(1, self.num_dios + 1))

    @property
    def odd_pin_range(self):
        return set(range(1, self.num_dios, 2))

    @property
    def even_pin_range(self):
        return self.pin_range - self.odd_pin_range

    def in_name(self, i):
        return 'in{}'.format(i)

    def out_name(self, i):
        return 'out{}'.format(i)

    def set_out(self, i, val=1):
        self.comp[self.out_name(i)] = val

    def clear_out(self, i):
        self.set_out(i, 0)

    def get_out(self, i):
        return self.comp[self.out_name(i)]

    def get_in(self, i):
        return self.comp[self.in_name(i)]

    def coalesce(self):
        time.sleep(self.coalescence_period)

    def blink(self):
        time.sleep(self.blink_period)

    def setup(self):
        self.logger.info("Setting up")
        self.comp = hal.component(self.comp_name)
        self.logger.debug("Initialized component")
        for i in self.pin_range:
            self.comp.newpin(self.in_name(i), hal.HAL_BIT, hal.HAL_IN)
            self.comp.newpin(self.out_name(i), hal.HAL_BIT, hal.HAL_OUT)
            self.clear_out(i)
        self.logger.debug("Initialized pins")
        # Track state of test
        self.state = [0] * self.num_dios
        self.last_state = [(-1, -1)] * self.num_dios
        self.comp.ready()
        self.logger.info("Ready to test")

    def clear_all(self):
        for i in self.pin_range:
            self.clear_out(i)

    def update_dio(self, i):
        cur_in = self.get_in(i)
        cur_out = self.get_out(i)
        if (cur_in, cur_out) != self.last_state[i]:
            self.logger.debug(
                "pin %d:  in-%d out-%d state-%d"
                % (i, cur_in, cur_out, self.state[i])
            )
            self.last_state[i] = (cur_in, cur_out)
        if cur_in:
            if cur_out:
                # input high, output high:  clear output and bump state
                self.clear_out(i)
                self.state[i] += 1
                self.logger.debug('Cleared output %d' % i)
                if self.state[i] == 2:
                    # successful test:  input followed output set and clear
                    self.logger.info("DIO {} test success".format(i))
            else:
                # input high, output low:  miswiring
                self.logger.warning("DIO {} miswired".format(i))
        else:
            if cur_out:
                # input low, output high:  test connector removed; reset state
                self.state[i] = 0
            else:
                # input low, output low:  set output
                self.set_out(i)

    def test_once(self, pin_idxs):
        # Test one or more pin indexes in sequence.
        # If any index passes, return True.

        # Phase 1:  Set each index output and clear all other outputs
        for idx in self.pin_range:
            self.set_out(idx, idx in pin_idxs)
        self.coalesce()

        # Phase 2:  Check that exactly one input is high
        high_inputs = set()
        for idx in self.pin_range:
            if self.get_in(idx):
                high_inputs.add(idx)
        if len(high_inputs) > 1:
            in_list = ",".join(["DIN_{}".format(i) for i in sorted(high_inputs)])
            self.logger.error("DOUT_{}:  multiple high inputs {}".format(idx, in_list))
            return None
        if len(high_inputs) < 1:
            # Not necessarily an error:  maybe test plug isn't connected
            return None
        high_input = high_inputs.pop()
        self.logger.debug("DIN_{} set".format(high_input))

        # Phase 3:  Check that input corresponds with output
        if not self.get_out(high_input):
            self.logger.error(
                "DIN_{} high, but DOUT_{} low".format(high_input, high_input)
            )
            return None
        for idx in self.pin_range:
            if idx == high_input:
                continue
            self.clear_out(idx)
        self.coalesce()
        if not self.get_in(high_input):
            self.logger.error(
                "DOUT_{} high, but DIN_{} low".format(high_input, high_input)
            )
            return None

        # Success!
        return high_input

    def test(self, pin_idxs, retry=False):
        # Test pin indexes with test_once().
        # If retry is True, keep trying until pass.
        # On success, return successful pin index.
        while True:
            res = self.test_once(pin_idxs)
            self.logger.debug(
                "Test result {} for indices {}".format(res, sorted(pin_idxs))
            )
            if res is not None:
                # Success; let LEDs glow for a moment and return
                self.blink()
                return res

            # Fail; dim all LEDs for a moment and return
            self.clear_all()
            self.blink()
            if not retry:
                return res

    def main(self):
        time.sleep(1)  # Leave time for setup to print other output
        try:
            while True:
                # Keep testing odd pins until one passes
                passing_idx = self.test(self.odd_pin_range, retry=True)
                # Test next higher (even) pin once
                self.test({passing_idx + 1}, retry=False)
        except KeyboardInterrupt:
            self.logger.info('Exiting component')
            sys.exit(0)


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
    comp = DIOTestComp()
    comp.setup()
    comp.main()
