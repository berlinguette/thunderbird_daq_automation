import { RepeatIcon } from '@chakra-ui/icons';
import { Box, Button, Card, CardBody, Checkbox, Flex, Table, TableContainer, Tbody, Td, Th, Thead, Tr } from '@chakra-ui/react';
import { useState } from 'react';

const testData = [
  {
    selected: false,
    id: "ID-420",
    props: {
      unconverted_mtime: "Apr 23, 2024 12:02 PM",
      converted_mtime: "Apr 23, 2024 12:02 PM",
      processed_mtime: "Apr 23, 2024 12:02 PM",
      overridden: false
    }
  },
  {
    selected: false,
    id: "ID-419",
    props: {
      unconverted_mtime: "Apr 23, 2024 12:02 PM",
      converted_mtime: "Apr 23, 2024 12:02 PM",
      processed_mtime: "Apr 23, 2024 12:02 PM",
      overridden: true
    }
  },
  {
    selected: false,
    id: "ID-418",
    props: {
      unconverted_mtime: "Apr 23, 2024 12:02 PM",
      converted_mtime: "-1",
      processed_mtime: "-1",
      overridden: false
    }
  }
];

const InventoryTable = () => {
  const [experiments, setExperiments] = useState(testData);

  const allChecked = experiments.every(({selected}) => selected);
  const isIndeterminate = experiments.some(({selected}) => selected) && !allChecked;
  const handleCheckAll = () => {
    const newChecked = isIndeterminate || !allChecked;
    setExperiments((prev) => prev.map((exp) => {
      return {
        ...exp,
        selected: newChecked
      };
    }));
  };

  const makeCheckedHandler = (index: number) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setExperiments((prev) => {
      const newExperiments = [...prev];
      newExperiments[index].selected = event.target.checked;
      return newExperiments;
    });
  };

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
                  <Th>ID</Th>
                  <Th>Unconverted Data</Th>
                  <Th>Converted Data</Th>
                  <Th>Processed Data</Th>
                </Tr>
              </Thead>
              <Tbody>
                {experiments.map((exp, i) => (
                  <Tr
                    bg={exp.selected ? "blue.50" : "transparent"}
                    key={exp.id}
                  >
                    <Td><Checkbox isChecked={exp.selected} onChange={makeCheckedHandler(i)} /></Td>
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
    </Flex>
  );
};

const MTimeDisplay = ({mtime, overridden}: {mtime: string, overridden: boolean}) => {
  const found = Number(mtime) !== -1;
  return (
    <Box color={found ? "green.600" : "red.600"}>
      {found ? mtime : "Not found"}
      {overridden && <Box color="orange.600">(Overridden)</Box>}
    </Box>
  )
}

export default InventoryTable;