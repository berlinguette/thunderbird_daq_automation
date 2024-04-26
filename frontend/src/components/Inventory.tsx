import { RepeatIcon } from "@chakra-ui/icons";
import { Button, Flex } from "@chakra-ui/react";
import InventoryTable from "./InventoryTable";
import { Experiment } from "../types/Experiment";
import { useEffect, useState } from "react";

const testData: Experiment[] = [
  {
    id: "ID-420",
    props: {
      unconverted_mtime: new Date("Apr 23, 2024 12:02 PM"),
      converted_mtime: new Date("Apr 23, 2024 12:03 PM"),
      processed_mtime: new Date("Apr 23, 2024 12:04 PM"),
      overridden: false
    }
  },
  {
    id: "ID-419",
    props: {
      unconverted_mtime: new Date("Jan 01, 1970 12:00 AM"),
      converted_mtime: new Date("Jan 01, 1970 12:00 AM"),
      processed_mtime: new Date("Jan 01, 1970 12:00 AM"),
      overridden: true
    }
  },
  {
    id: "ID-418",
    props: {
      unconverted_mtime: new Date("Apr 23, 2024 12:02 PM"),
      converted_mtime: -1,
      processed_mtime: -1,
      overridden: false
    }
  },
  {
    id: "ID-TEST",
    props: {
      unconverted_mtime: new Date("Apr 23, 2024 12:02 PM"),
      converted_mtime: -1,
      processed_mtime: -1,
      overridden: false
    }
  }
];

export type CheckedExperiments = { [id: string]: boolean }

const Inventory = () => {
  const [checkedExperiments, setCheckedExperiments] = useState<CheckedExperiments>({});

  /** Keeps checkedExperiments' number of entries up to date with latest list of experiments */
  useEffect(() => {
    const initialValue = {} as CheckedExperiments; // for intellisense :3
    setCheckedExperiments((prev) => testData.reduce((acc, curr) => {
      return {
        ...acc,
        [curr.id]: prev[curr.id] ?? false
      }
    }, initialValue));
  }, []);

  return (
    <Flex flexDir="column" gap={4}>
      <Flex gap={6} padding={4}>
        <Button colorScheme="blue">Analyze All</Button>
        <Button colorScheme="blue" variant="outline">Analyze Selected</Button>
        <Button variant="ghost" gap={2} color="grey">
          Refresh Inventory
          <RepeatIcon boxSize={5} />
        </Button>
      </Flex>
      <InventoryTable
        experimentsList={testData}
        checkedExperiments={checkedExperiments}
        setCheckedExperiments={setCheckedExperiments}
      />
    </Flex>
  )
};

export default Inventory;