import { RepeatIcon } from "@chakra-ui/icons";
import { Button, Flex, Spacer } from "@chakra-ui/react";
import InventoryTable from "./InventoryTable";
import { Experiment } from "../types/Experiment";
import { useEffect, useState } from "react";
import OverridesPanel from "./OverridesPanel";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getInventory } from "../api/inventory";
import { InventoryFilter } from "../api/inventory";
import AnalyzeMenu from "./AnalyzeMenu";

// const testData: Experiment[] = [
//   {
//     id: "ID-420",
//     props: {
//       unconverted_mtime: 1714171417,
//       converted_mtime: 1714171417,
//       processed_mtime: 1714171417,
//       overridden: false
//     }
//   },
//   {
//     id: "ID-419",
//     props: {
//       unconverted_mtime: 0,
//       converted_mtime: 0,
//       processed_mtime: 0,
//       overridden: true
//     }
//   },
//   {
//     id: "ID-418",
//     props: {
//       unconverted_mtime: 1714171417,
//       converted_mtime: -1,
//       processed_mtime: -1,
//       overridden: false
//     }
//   },
//   {
//     id: "ID-TEST",
//     props: {
//       unconverted_mtime: 1714171417,
//       converted_mtime: -1,
//       processed_mtime: -1,
//       overridden: false
//     }
//   }
// ];

export type CheckedExperiments = { [id: string]: boolean }

const Inventory = ({ filter = undefined }: { filter?: InventoryFilter }) => {
  const queryClient = useQueryClient();
  const { isPending, isError, data, error } = useQuery({
    queryKey: ["inventory"],
    queryFn: () => getInventory(filter)
  });
  const [checkedExperiments, setCheckedExperiments] = useState<CheckedExperiments>({});

  /** Keeps checkedExperiments' number of entries up to date with latest list of experiments */
  useEffect(() => {
    if (data) {
      setCheckedExperiments((prev) => data.reduce((acc: CheckedExperiments, curr: Experiment) => {
        return {
          ...acc,
          [curr.id]: prev[curr.id] ?? false
        }
      }, {}));
    }
  }, [data]);

  const handleRefreshInventory = () => {
    queryClient.invalidateQueries({ queryKey: ["inventory"] });
  }

  if (isPending) {
    return <p>Loading experiments...</p>;
  }

  if (isError) {
    return <p>Error while loading experiments: {error.message}</p>
  }

  return (
    <Flex flexDir="column" gap={4}>
      <Flex gap={6} padding={4}>
        <AnalyzeMenu analyzeFilter="all" checkedExperiments={checkedExperiments} />
        <AnalyzeMenu
          analyzeFilter="selected"
          checkedExperiments={checkedExperiments}
          disabled={Object.values(checkedExperiments).every((v) => !v)}
          outline
        />
        <Button variant="ghost" gap={2} color="grey" onClick={handleRefreshInventory}>
          Refresh Inventory
          <RepeatIcon boxSize={5} />
        </Button>
        <Spacer />
        <OverridesPanel />
      </Flex>
      <InventoryTable
        experimentsList={data}
        checkedExperiments={checkedExperiments}
        setCheckedExperiments={setCheckedExperiments}
      />
    </Flex>
  )
};

export default Inventory;