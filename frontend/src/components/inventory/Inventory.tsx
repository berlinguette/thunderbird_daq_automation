import { Button, Flex, Spacer, Spinner } from "@chakra-ui/react";
import InventoryTable from "./InventoryTable";
import { Experiment } from "../../types/Experiment";
import { useEffect, useState } from "react";
import OverridesPanel from "../OverridesPanel";
import { useQuery } from "@tanstack/react-query";
import { getInventory } from "../../api/inventory";
import { InventoryFilter } from "../../api/inventory";
import AnalyzeMenu from "../AnalyzeMenu";

export type CheckedExperiments = { [id: string]: boolean }

const Inventory = ({ filter = undefined }: { filter?: InventoryFilter }) => {
  const { isPending, isFetching, isError, data, error, refetch } = useQuery({
    queryKey: ["inventory", filter],
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
    refetch();
  }

  return (
    <Flex flexDir="column" gap={4} height="100%">
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
          {isFetching && <Spinner size="sm" speed="0.6s" />}
        </Button>
        <Spacer />
        <OverridesPanel refetchInventory={refetch} />
      </Flex>
      {isPending && <p>Loading experiments...</p>}
      {isError && <p>Error while loading experiments: {error.message}</p>}
      {!isPending && !isError && data &&
        <InventoryTable
          experimentsList={data}
          checkedExperiments={checkedExperiments}
          setCheckedExperiments={setCheckedExperiments}
        />
      }
    </Flex>
  );
};

export default Inventory;