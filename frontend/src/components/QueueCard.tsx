import { Card, CardBody, Flex, HStack, Text } from "@chakra-ui/react";
import { Analysis } from "../types/Analysis";
import { useAnalysisSteps } from "../hooks/useAnalysisSteps";

const QueueCard = ({
  analysis,
  inProgress = false,
}: {
  analysis: Analysis;
  inProgress?: boolean;
}) => {
  const { steps } = useAnalysisSteps();

  return (
    <Card variant="filled" marginX={4}>
      <CardBody>
        <Flex justifyContent="space-around" fontWeight={600}>
          <Text>{analysis.exp_id}</Text>
          {steps?.slice(0, -1).map((step, i) => {
            const willAnalyzeCurrentStep = analysis.params.steps_to_analyze[i];
            let displayText = willAnalyzeCurrentStep ? "Yes" : "No";
            let displayColor = willAnalyzeCurrentStep ? "green.600" : "red.600";

            if (inProgress) {
              if (analysis.current_step > i) {
                displayText = "Done";
                displayColor = "green.600";
              } else if (analysis.current_step < i) {
                displayText = "Waiting";
                displayColor = "black";
              } else {
                displayText = "In Progress";
                displayColor = "yellow.600";
              }
            }
            return (
              <HStack>
                <Text>{step}</Text>
                <Text fontWeight={400} color={displayColor}>
                  {displayText}
                </Text>
              </HStack>
            );
          })}
        </Flex>
      </CardBody>
    </Card>
  );
};

export default QueueCard;
