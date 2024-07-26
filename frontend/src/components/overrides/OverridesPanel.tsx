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
import {
  FlattenedOverride,
  flattenOverride,
  unflattenOverride,
} from "./flattenedOverride";

const OverridesPanel = ({
  refetchInventory,
}: {
  refetchInventory: () => void;
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [overrides, setOverrides] = useState<FlattenedOverride[]>([]);
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

  const reloadData = useCallback(async () => {
    await refetchOverrides();
    if (fetchedOverrides) {
      setOverrides(fetchedOverrides.map(flattenOverride));
    }
  }, [fetchedOverrides, refetchOverrides]);

  const onOpenModal = async () => {
    await reloadData();
    onOpen();
  };

  const onAddOverride = () => {
    setOverrides((prev) => [
      ...prev,
      {
        pattern: "",
        unconverted_mtime: "",
        converted_mtime: "",
        processed_mtime: "",
      },
    ]);
  };

  const onSavePanel = async () => {
    if (fetchedOverrides) {
      const ovrToDelete = fetchedOverrides.filter(
        (exp) => !overrides.find((ovrExp) => exp.id === ovrExp.pattern)
      );
      for (const ovr of ovrToDelete) {
        await deleteOvrMutation.mutateAsync(ovr.id);
      }
      for (const ovr of overrides) {
        if (ovr.pattern === "") {
          setFormErr("Pattern cannot be blank");
          return;
        }
        const newOvr = unflattenOverride(ovr);
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
            {!isPending && !isError && fetchedOverrides && (
              <Grid templateColumns="0.1fr repeat(4, 1fr)" gap={2}>
                <GridItem />
                <GridItem>Pattern</GridItem>
                <GridItem>Unconverted Data Modified Time</GridItem>
                <GridItem>Converted Data Modified Time</GridItem>
                <GridItem>Processed Data Modified Time</GridItem>

                {overrides.map((override, i) => (
                  <Override
                    override={override}
                    index={i}
                    setOverrides={setOverrides}
                    key={i}
                  />
                ))}
              </Grid>
            )}
            <Button
              marginTop={4}
              colorScheme="green"
              onClick={onAddOverride}
            >
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
