#!/usr/bin/env python3

import sys
import csv
from pprint import pformat
import argparse
import logging


class Correlator:
    def __init__(self, ecat_csv_fname, sampler_csv_fname):
        self.ecat_csv_fname = ecat_csv_fname
        self.sampler_csv_fname = sampler_csv_fname
        self.samples = dict()
        self.logger = logging.getLogger(__name__)

    def read_ecat(self, counter_field):
        self.logger.info(f"Reading EtherCAT CSV from {self.ecat_csv_fname}")
        self.logger.info(f"Counter field:  {counter_field}")
        with open(self.ecat_csv_fname) as f:
            reader = csv.DictReader(f, quoting=csv.QUOTE_NONNUMERIC)
            self.logger.debug(f"Field names:  {reader.fieldnames}")
            first_counter = None
            for row in reader:
                counter = int(row.get(counter_field))
                sample = self.samples.setdefault(counter, dict())
                ecat_sample = sample.setdefault("ecat", list())
                ecat_sample.append(row)
                if first_counter is None:
                    first_counter = counter
            last_counter = counter
            self.ecat_fieldnames = reader.fieldnames

        # Remove first & last samples if not exactly two
        for counter in first_counter, last_counter:
            if len(self.samples[counter]["ecat"]) != 2:
                self.samples.pop(counter)

    def print_samples(self, max_lines=None):
        for counter, vals in self.samples.items():
            if max_lines is not None:
                if max_lines <= 0:
                    break
                max_lines -= 1
            print(pformat(vals))

    def print_ecat_abnormal(self):
        def print_sample(reason, counter, num_vals, ecat_vals):
            self.logger.warn("Abnormal:", reason)
            self.logger.warn(counter, num_vals)
            self.logger.warn(pformat(ecat_vals))

        prev_counter = None
        num_abnormal = 0
        for counter, vals in self.samples.items():
            if "ecat" not in vals:
                continue
            abnormal = False
            ecat_vals = vals["ecat"]
            num_vals = len(ecat_vals)
            if num_vals != 2:
                print_sample(
                    f"{num_vals} ECAT pkts", counter, num_vals, ecat_vals
                )
                abnormal = True
            if prev_counter is not None and counter != prev_counter + 1:
                reason = f"cur={counter}, prev={prev_counter}"
                print_sample(reason, counter, num_vals, ecat_vals)
                abnormal = True

            prev_counter = counter
            if abnormal:
                num_abnormal += 1
        if num_abnormal:
            self.logger.warn(f"Found {num_abnormal} abnormal samples")
        else:
            self.logger.info("No abnormal samples found")

    def read_sampler(self, counter_field="counter"):
        self.logger.info(
            f"Reading halsampler CSV from {self.sampler_csv_fname}"
        )
        self.logger.info(f"Counter field:  {counter_field}")
        with open(self.sampler_csv_fname) as f:
            reader = csv.DictReader(f, quoting=csv.QUOTE_NONNUMERIC)
            self.logger.debug(f"Field names:  {reader.fieldnames}")
            for row in reader:
                counter = int(row.get(counter_field))
                sample = self.samples.setdefault(counter, dict())
                sample["sampler"] = row
            self.sampler_fieldnames = reader.fieldnames

    def trim_ecat_sampler(self):
        total_samples = len(self.samples)
        to_pop = set()
        for counter, vals in self.samples.items():
            if "ecat" not in vals or "sampler" not in vals:
                to_pop.add(counter)
        invalid_samples = len(to_pop)
        for counter in to_pop:
            self.samples.pop(counter)
        self.logger.info(
            f"Threw away {invalid_samples} incomplete samples"
            f" of {total_samples}"
        )

    @property
    def num_samples(self):
        return len(self.samples)

    def collate(self):
        self.collated = dict()
        for counter, vals in self.samples.items():
            new_vals = self.collated[counter] = vals["sampler"].copy()
            for e_vals in vals["ecat"]:
                prefix = "m." if e_vals["src_master"] == "True" else "s."
                for k, v in e_vals.items():
                    pk = prefix + k
                    assert pk not in new_vals, f"Dup at {counter}"
                    new_vals[pk] = v
        self.collate_fieldnames = (
            self.sampler_fieldnames
            + [f"m.{i}" for i in self.ecat_fieldnames]
            + [f"s.{i}" for i in self.ecat_fieldnames]
        )
        self.logger.info(f"Total valid samples:  {len(self.collated)}")

    def write_collated(self, fname):
        self.logger.info(f"Writing output to {fname}")
        with open(fname, "w") as f:
            writer = csv.DictWriter(f, fieldnames=self.collate_fieldnames)
            writer.writeheader()
            for row in self.collated.values():
                writer.writerow(row)

    @classmethod
    def cli(cls):
        parser = argparse.ArgumentParser(
            description='Correlate samples from halsampler and ethercat pcap.'
        )

        parser.add_argument(
            "--halsampler-csv",
            type=str,
            help="halsampler CSV input filename",
        )
        parser.add_argument(
            "--halsampler-counter-field",
            type=str,
            help="halsampler CSV counter column name",
        )
        parser.add_argument(
            "--ethercat-csv",
            type=str,
            help="EtherCAT CSV input filename",
        )
        parser.add_argument(
            "--ethercat-counter-field",
            type=str,
            help="EtherCAT CSV counter column name",
        )
        parser.add_argument(
            "--output-csv",
            type=str,
            help="Output CSV filename",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Set log level to debug",
        )

        args = parser.parse_args()
        logging.basicConfig()
        obj = cls(args.ethercat_csv, args.halsampler_csv)
        obj.logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
        obj.read_ecat(args.ethercat_counter_field)
        obj.read_sampler(args.halsampler_counter_field)
        obj.trim_ecat_sampler()
        obj.print_ecat_abnormal()
        obj.collate()
        obj.write_collated(args.output_csv)


if __name__ == "__main__":
    sys.exit(Correlator.cli())
