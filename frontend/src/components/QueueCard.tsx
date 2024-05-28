import { Card, CardBody, Flex, HStack, Text } from "@chakra-ui/react";
import { Analysis } from "../types/Analysis";

const QueueCard = ({ analysis, inProgress = false }: { analysis: Analysis, inProgress?: boolean }) => {
  const convert = analysis.params.convert_unconverted;
  const process = analysis.params.process_converted;

  let convertDisplayText = convert ? "Yes" : "No";
  let convertDisplayColor = convert ? "green.600" : "red.600";
  let processDisplayText = process ? "Yes" : "No";
  let processDisplayColor = convert ? "green.600" : "red.600";
  if (inProgress) {
    if (analysis.stage === "convert") {
      convertDisplayText = "In Progress";
      convertDisplayColor = "yellow.600";
      processDisplayText = "Waiting";
      processDisplayColor = "black";
    } else {
      convertDisplayText = "Done";
      convertDisplayColor = "green.600";
      processDisplayText = "In Progress";
      processDisplayColor = "yellow.600";
    }
  }
  return (
    <Card variant="filled" marginX={4}>
      <CardBody>
        <Flex justifyContent="space-around" fontWeight={600}>
          <Text>{analysis.exp.id}</Text>
          <HStack>
            <Text>Convert: </Text>
            <Text fontWeight={400} color={convertDisplayColor}>{convertDisplayText}</Text>
          </HStack>
          <HStack>
            <Text>Process: </Text>
            <Text fontWeight={400} color={processDisplayColor}>{processDisplayText}</Text>
          </HStack>
        </Flex>
      </CardBody>
    </Card>
  );
};

export default QueueCard;