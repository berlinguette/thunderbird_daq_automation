import { SettingsIcon } from "@chakra-ui/icons";
import {
  Button,
  Grid,
  GridItem,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
  useDisclosure,
} from "@chakra-ui/react";
import { useCallback, useEffect, useState } from "react";
import useOverrides from "../../hooks/useOverrides";
import Override from "./Override";
import { useAnalysisSteps } from "../../hooks/useAnalysisSteps";
import { makeStrictOverride, makeUnstrictOverride, UnstrictOverride } from "./unstrictOverride";

const OverridesPanel = ({
  refetchInventory,
}: {
  refetchInventory: () => void;
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [unstrictOverrides, setUnstrictOverrides] = useState<
    UnstrictOverride[]
  >([]);
  const [formErr, setFormErr] = useState<string | null>(null);
  const {
    isPending,
    isError,
    overrides: fetchedOverrides,
    error,
    refetchOverrides,
    deleteOvrMutation,
    addOvrMutation,
  } = useOverrides();
  const { steps } = useAnalysisSteps();

  const reloadData = useCallback(async () => {
    await refetchOverrides();
    if (fetchedOverrides) {
      setUnstrictOverrides(fetchedOverrides.map(makeUnstrictOverride));
    }
  }, [fetchedOverrides, refetchOverrides]);

  const onOpenModal = async () => {
    await reloadData();
    onOpen();
  };

  const onAddOverride = () => {
    setUnstrictOverrides((prev) => [
      ...prev,
      {
        pattern: "",
        analysis_step_overrides:
          steps?.map(() => ({
            mtime: "",
          })) ?? [],
      },
    ]);
  };

  const onSavePanel = async () => {
    if (fetchedOverrides) {
      const ovrToDelete = fetchedOverrides.filter(
        (ovr) =>
          !unstrictOverrides.find(
            (unstrictOvr) => ovr.pattern === unstrictOvr.pattern
          )
      );
      for (const ovr of ovrToDelete) {
        await deleteOvrMutation.mutateAsync(ovr.pattern);
      }
      for (const ovr of unstrictOverrides) {
        if (ovr.pattern === "") {
          setFormErr("Pattern cannot be blank");
          return;
        }
        const newOvr = makeStrictOverride(ovr);
        await addOvrMutation.mutateAsync(newOvr);
      }
    }
    if (!deleteOvrMutation.isError && !addOvrMutation.isError) {
      onClose();
      refetchInventory();
    }
  };

  useEffect(() => {
    reloadData();
    setFormErr(null);
  }, [reloadData]);

  return (
    <>
      <Button
        colorScheme="orange"
        leftIcon={<SettingsIcon />}
        onClick={onOpenModal}
      >
        Manage Overrides
      </Button>

      <Modal isOpen={isOpen} onClose={onClose} closeOnOverlayClick={false}>
        <ModalOverlay />
        <ModalContent maxW="80vw">
          <ModalHeader>Manage Overrides</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {isPending && <p>Loading...</p>}
            {isError && (
              <p>
                <span>An error occurred when fetching data:</span>{" "}
                {error?.message}
              </p>
            )}
            {!isPending && !isError && fetchedOverrides && steps && (
              <Grid
                templateColumns={`0.1fr repeat(${steps.length + 1}, 1fr)`}
                gap={2}
              >
                <GridItem />
                <GridItem>Pattern</GridItem>
                {steps.map((step) => (
                  <GridItem>{step} Modified Time</GridItem>
                ))}

                {unstrictOverrides.map((override, i) => (
                  <Override
                    unstrictOverride={override}
                    steps={steps}
                    index={i}
                    setUnstrictOverrides={setUnstrictOverrides}
                    key={i}
                  />
                ))}
              </Grid>
            )}
            <Button marginTop={4} colorScheme="green" onClick={onAddOverride}>
              + Add Override
            </Button>
          </ModalBody>

          <ModalFooter>
            {formErr && <Text mr={3}>{formErr}</Text>}
            {deleteOvrMutation.isError && (
              <Text mr={3}>{deleteOvrMutation.error.message}</Text>
            )}
            {addOvrMutation.isError && (
              <Text mr={3}>{addOvrMutation.error.message}</Text>
            )}
            <Button onClick={onClose} mr={3}>
              Cancel
            </Button>
            <Button
              onClick={onSavePanel}
              colorScheme="blue"
              isLoading={
                deleteOvrMutation.isPending || addOvrMutation.isPending
              }
            >
              Save
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default OverridesPanel;
