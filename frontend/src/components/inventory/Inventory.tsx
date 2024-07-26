import { Button, Flex, Spacer, Spinner } from "@chakra-ui/react";
import InventoryTable from "./InventoryTable";
import { Experiment } from "../../types/Experiment";
import { useEffect, useState } from "react";
import OverridesPanel from "../overrides/OverridesPanel";
import AnalyzeMenu from "../AnalyzeMenu";
import useInventory, { InventoryFilter } from "../../hooks/useInventory";

export type CheckedExperiments = { [id: string]: boolean };

const Inventory = ({ filter = undefined }: { filter?: InventoryFilter }) => {
  const { isPending, isFetching, inventory, isError, error, refetchInventory } =
    useInventory(filter);
  const [checkedExperiments, setCheckedExperiments] =
    useState<CheckedExperiments>({});

  /** Keeps checkedExperiments' number of entries up to date with latest list of experiments */
  useEffect(() => {
    if (inventory) {
      setCheckedExperiments((prev) =>
        inventory.reduce((acc: CheckedExperiments, curr: Experiment) => {
          return {
            ...acc,
            [curr.id]: prev[curr.id] ?? false,
          };
        }, {})
      );
    }
  }, [inventory]);

  const handleRefreshInventory = () => refetchInventory();

  return (
    <Flex flexDir="column" gap={4} height="100%">
      <Flex gap={6} padding={4}>
        <AnalyzeMenu
          analyzeFilter="all"
          checkedExperiments={checkedExperiments}
        />
        <AnalyzeMenu
          analyzeFilter="selected"
          checkedExperiments={checkedExperiments}
          disabled={Object.values(checkedExperiments).every((v) => !v)}
          outline
        />
        <Button
          variant="ghost"
          gap={2}
          color="grey"
          onClick={handleRefreshInventory}
        >
          Refresh Inventory
          {isFetching && <Spinner size="sm" speed="0.6s" />}
        </Button>
        <Spacer />
        <OverridesPanel refetchInventory={refetchInventory} />
      </Flex>
      {isPending && <p>Loading experiments...</p>}
      {isError && <p>Error while loading experiments: {error?.message}</p>}
      {!isPending && !error && inventory && (
        <InventoryTable
          experimentsList={inventory}
          checkedExperiments={checkedExperiments}
          setCheckedExperiments={setCheckedExperiments}
        />
      )}
    </Flex>
  );
};

export default Inventory;
