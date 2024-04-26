import { ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
import { Box, Card, CardBody, Checkbox, Table, TableContainer, Tbody, Td, Th, Thead, Tr } from '@chakra-ui/react';
import { useEffect, useState } from 'react';
import { Experiment } from '../types/Experiment';
import { CheckedExperiments } from './Inventory';

type Conversions = "unconverted" | "converted" | "processed";

/** Possible sort states of the table.
 * The non `-rev` versions will sort in order of newest to oldest
 * while the `-rev` versions will sort from oldest to newest. */
type Sort = "id" | Conversions;

type InventoryTableProps = {
  experimentsList: Experiment[],
  checkedExperiments: CheckedExperiments,
  setCheckedExperiments: React.Dispatch<React.SetStateAction<CheckedExperiments>>
};

const InventoryTable = ({ experimentsList, checkedExperiments, setCheckedExperiments }: InventoryTableProps) => {
  const [experiments, setExperiments] = useState<Experiment[]>(experimentsList);
  const [sort, setSort] = useState<Sort>("id");
  const [reverseSort, setReverseSort] = useState(false);

  const allChecked = Object.values(checkedExperiments).every(Boolean);
  const isIndeterminate = Object.values(checkedExperiments).some(Boolean) && !allChecked;

  const handleCheckAll = () => {
    const newChecked = isIndeterminate || !allChecked;
    setCheckedExperiments((prev) => {
      const newCheckedExperiments = {...prev};
      Object.keys(newCheckedExperiments).forEach((key) => newCheckedExperiments[key] = newChecked);
      return newCheckedExperiments;
    });
  };

  const makeCheckedHandler = (id: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setCheckedExperiments((prev) => {
      return {
        ...prev,
        [id]: event.target.checked
      };
    });
  };

  const makeColumnClickHandler = (columnName: "id" | "unconverted" | "converted" | "processed") => () => {
    if (sort === columnName) {
      setReverseSort((prev) => !prev);
    } else {
      setSort(columnName);
      setReverseSort(false);
    }
  }

  /** Sorts experiment IDs in the format `ID-xxx` in descending order (most recent first).
   * Experiments with non-numeric IDs will be sorted to the end. */
  const experimentSorter = (a: Experiment, b: Experiment) => {
    const aId = a.id.split("-")[1];
    const bId = b.id.split("-")[1];
    if (!aId || isNaN(parseInt(aId))) return 1;
    if (!bId || isNaN(parseInt(bId))) return -1;

    return Number(bId) - Number(aId);
  }

  /** Makes an experiment sorter based on the desired type to sort by.
   * Non `-rev` versions will sort in descending order (most recent first).
   */
  const makeMtimeSorter = (type: Conversions) => (a: Experiment, b: Experiment) => {
    let aMtime = a.props.unconverted_mtime;
    let bMtime = b.props.unconverted_mtime;
    if (type === "converted") {
      aMtime = a.props.converted_mtime;
      bMtime = b.props.converted_mtime;
    }
    if (type === "processed") {
      aMtime = a.props.processed_mtime;
      bMtime = b.props.processed_mtime;
    }

    if (aMtime == -1 && bMtime == -1) return 0;
    if (aMtime == -1) return 1;
    if (bMtime == -1) return -1;
    return bMtime.valueOf() - aMtime.valueOf();
  }

  useEffect(() => {
    // In-place sorting/reverse functions cause weird behavior :/
    let sortedExperiment = experimentsList;
    switch (sort) {
      case "id":
        sortedExperiment = sortedExperiment.toSorted(experimentSorter);
        break;
      default:
        sortedExperiment = sortedExperiment.toSorted(makeMtimeSorter(sort));
    }
    if (reverseSort) sortedExperiment = sortedExperiment.toReversed();
    setExperiments(sortedExperiment);
  }, [sort, reverseSort, experimentsList]);

  return (
    <Card variant="outline">
      <CardBody>
        <TableContainer>
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>
                  <Checkbox
                    isChecked={allChecked}
                    isIndeterminate={isIndeterminate}
                    onChange={handleCheckAll}
                  />
                </Th>
                <Th>
                  <Box cursor="pointer" onClick={makeColumnClickHandler("id")}>
                    ID
                    {sort === "id" && !reverseSort && <ChevronDownIcon boxSize={5} />}
                    {sort === "id" && reverseSort && <ChevronUpIcon boxSize={5} />}
                  </Box>
                </Th>
                <Th>
                  <Box cursor="pointer" onClick={makeColumnClickHandler("unconverted")}>
                    Unconverted Data
                    {sort === "unconverted" && !reverseSort && <ChevronDownIcon boxSize={5} />}
                    {sort === "unconverted" && reverseSort && <ChevronUpIcon boxSize={5} />}
                  </Box>
                </Th>
                <Th>
                  <Box cursor="pointer" onClick={makeColumnClickHandler("converted")}>
                    Converted Data
                    {sort === "converted" && !reverseSort && <ChevronDownIcon boxSize={5} />}
                    {sort === "converted" && reverseSort && <ChevronUpIcon boxSize={5} />}
                  </Box>
                </Th>
                <Th>
                  <Box cursor="pointer" onClick={makeColumnClickHandler("processed")}>
                    Processed Data
                    {sort === "processed" && !reverseSort && <ChevronDownIcon boxSize={5} />}
                    {sort === "processed" && reverseSort && <ChevronUpIcon boxSize={5} />}
                  </Box>
                </Th>
              </Tr>
            </Thead>
            <Tbody>
              {experiments.map((exp) => (
                <Tr
                  bg={checkedExperiments[exp.id] ? "blue.50" : "transparent"}
                  key={exp.id}
                >
                  <Td><Checkbox isChecked={checkedExperiments[exp.id]} onChange={makeCheckedHandler(exp.id)} /></Td>
                  <Td>{exp.id}</Td>
                  <Td>
                    <MTimeDisplay mtime={exp.props.unconverted_mtime} overridden={exp.props.overridden} />
                  </Td>
                  <Td>
                    <MTimeDisplay mtime={exp.props.converted_mtime} overridden={exp.props.overridden} />
                  </Td>
                  <Td>
                    <MTimeDisplay mtime={exp.props.processed_mtime} overridden={exp.props.overridden} />
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </TableContainer>
      </CardBody>
    </Card>
  );
};

const MTimeDisplay = ({ mtime, overridden }: { mtime: Date | -1, overridden: boolean }) => {
  const found = mtime != -1;
  return (
    <Box color={found ? "green.600" : "red.600"}>
      {found ? mtime.toLocaleString() : "Not found"}
      {overridden && <Box color="orange.600">(Overridden)</Box>}
    </Box>
  )
}

export default InventoryTable;