import {
  Button,
  Checkbox,
  CheckboxGroup,
  Flex,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  useCheckboxGroup,
  useDisclosure,
} from "@chakra-ui/react";
import { CheckedExperiments } from "./inventory/Inventory";
import { AnalysisRequestParams } from "../types/Analysis";
import { useNavigate } from "react-router-dom";
import { useMutateAnalyses } from "../hooks/useAnalyses";
import { useAnalysisSteps } from "../hooks/useAnalysisSteps";
import { useState } from "react";

type AnalyzeMenuProps = {
  analyzeFilter: "all" | "selected";
  checkedExperiments: CheckedExperiments;
  disabled?: boolean;
  outline?: boolean;
};

const AnalyzeMenu = ({
  analyzeFilter,
  checkedExperiments,
  disabled = false,
  outline = false,
}: AnalyzeMenuProps) => {
  const navigate = useNavigate();
  const { mutation } = useMutateAnalyses();
  const { steps } = useAnalysisSteps();
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { value, getCheckboxProps } = useCheckboxGroup();

  const analyzeHandler = async () => {
    if (!steps) return;
    if (value.length == 0) {
      setAnalysisError("Must select at least one step to analyze");
      return;
    }
    setAnalysisError(null);

    const body: AnalysisRequestParams = {
      steps_to_analyze: steps.slice(0, -1).map((step) => value.includes(step)),
    };

    if (analyzeFilter !== "all") {
      const checkedIds = Object.entries(checkedExperiments).map(
        ([id, checked]) => (checked ? id : "")
      );
      body.pattern = `(${checkedIds.filter((v) => v !== "").join("|")})`;
    }
    mutation.mutate(body, { onSuccess: () => navigate("/queue") });
  };

  return (
    <>
      <Button
        colorScheme="blue"
        isDisabled={disabled}
        isLoading={mutation.isPending}
        variant={outline ? "outline" : "solid"}
        onClick={onOpen}
      >
        Analyze {analyzeFilter == "all" ? "All" : "Selected"}
      </Button>
      {steps && (
        <Modal onClose={onClose} isOpen={isOpen}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>
              Select steps for analyzing{" "}
              {analyzeFilter == "all" ? "all" : "selected"}
            </ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {steps.slice(0, -1).map((step) => (
                <CheckboxGroup value={value}>
                  <Stack>
                    <Checkbox {...getCheckboxProps({ value: step })}>
                      {step}
                    </Checkbox>
                  </Stack>
                </CheckboxGroup>
              ))}
            </ModalBody>
            <ModalFooter>
              <Stack gap={2} width="100%">
                {analysisError && <Text fontSize="sm" color="red">{analysisError}</Text>}
                <Flex gap={4} width="100%" justify="end">
                  <Button onClick={onClose}>Cancel</Button>
                  <Button onClick={analyzeHandler} colorScheme="blue">
                    Analyze
                  </Button>
                </Flex>
              </Stack>
            </ModalFooter>
          </ModalContent>
        </Modal>
      )}
      {mutation.isError && <p>{mutation.error.message}</p>}
    </>
  );
};

export default AnalyzeMenu;
