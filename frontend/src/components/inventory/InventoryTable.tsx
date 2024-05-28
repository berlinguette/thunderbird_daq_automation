import { ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
import { Box, Card, CardBody, Checkbox, Table, TableContainer, Tbody, Td, Th, Thead, Tooltip, Tr } from '@chakra-ui/react';
import { useEffect, useState } from 'react';
import { Experiment } from '../../types/Experiment';
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
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [sort, setSort] = useState<Sort>("id");
  const [reverseSort, setReverseSort] = useState(false);

  const allChecked = Object.values(checkedExperiments).every(Boolean);
  const isIndeterminate = Object.values(checkedExperiments).some(Boolean) && !allChecked;

  const handleCheckAll = () => {
    const newChecked = !allChecked;
    setCheckedExperiments((prev) => {
      const newCheckedExperiments = { ...prev };
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
    if (!aId || isNaN(Number(aId))) return 1;
    if (!bId || isNaN(Number(bId))) return -1;

    return Number(bId) - Number(aId);
  }

  /** Makes an experiment sorter based on the desired type to sort by.
   * Non `-rev` versions will sort in descending order (most recent first).
   */
  const makeMtimeSorter = (type: Conversions) => (a: Experiment, b: Experiment) => {
    let aMTime = a.props.unconverted_mtime;
    let bMTime = b.props.unconverted_mtime;
    if (type === "converted") {
      aMTime = a.props.converted_mtime;
      bMTime = b.props.converted_mtime;
    }
    if (type === "processed") {
      aMTime = a.props.processed_mtime;
      bMTime = b.props.processed_mtime;
    }
    if (aMTime === "Error") return 1;
    if (bMTime === "Error") return -1;

    return bMTime - aMTime;
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
    <Card variant="outline" overflowY="scroll" maxHeight="66dvh">
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
                  bg="white"
                  filter={checkedExperiments[exp.id] ? "brightness(90%)" : "none"}
                  key={exp.id}
                >
                  <Td><Checkbox isChecked={checkedExperiments[exp.id]} onChange={makeCheckedHandler(exp.id)} /></Td>
                  <Td>{exp.id}</Td>
                  <MTimeDisplay mtime={exp.props.unconverted_mtime} overridden={exp.props.overridden} />
                  <MTimeDisplay mtime={exp.props.converted_mtime} overridden={exp.props.overridden} />
                  <MTimeDisplay mtime={exp.props.processed_mtime} overridden={exp.props.overridden} />
                </Tr>
              ))}
            </Tbody>
          </Table>
        </TableContainer>
      </CardBody>
    </Card>
  );
};

const MTimeDisplay = ({ mtime, overridden }: { mtime: number | string, overridden: boolean }) => {
  const found = mtime != -1;
  const error = mtime === "Error";
  return (
    <Td
      fontWeight={600}
      bg={overridden ? "yellow.200" : error ? "orange.200" : found ? "green.200" : "red.200"}
      color={overridden ? "yellow.800" : error ? "orange.800" : found ? "green.800" : "red.800"}
    >
      <Tooltip
        openDelay={150}
        label={
          error ? "May be malformed - check experiment directory" :
          found ? `Directory last modified on ${new Date(mtime).toLocaleString()}` :
          "Directory not found in QMI storage"
        }
      >
        <Box>
          {error ? "Malformed" : found ? new Date(mtime).toLocaleString() : "Not found"}
          {overridden && <Box>(Overridden)</Box>}
        </Box>
      </Tooltip>
    </Td>
  );
};

export default InventoryTable;