import { QuestionIcon, SettingsIcon } from "@chakra-ui/icons";
import { Button, Grid, GridItem, Input, InputGroup, InputLeftAddon, Modal, ModalBody, ModalCloseButton, ModalContent, ModalFooter, ModalHeader, ModalOverlay, Popover, PopoverBody, PopoverContent, PopoverTrigger, Text, useDisclosure } from "@chakra-ui/react";
import { Experiment } from "../types/Experiment";
import { useCallback, useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { addOverride, deleteOverride, getOverrides } from "../api/overrides";

type Overrides = {
  pattern: string,
  unconverted_mtime: string,
  converted_mtime: string,
  processed_mtime: string
}

const OverridesPanel = ({ refetchInventory }: { refetchInventory: () => void }) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [overrides, setOverrides] = useState<Overrides[]>([]);
  const [formErr, setFormErr] = useState<string|null>(null);

  const { isPending, isError, data, error, refetch } = useQuery({
    queryKey: ["overrides"],
    queryFn: getOverrides,
    staleTime: Infinity
  });
  const deleteOvrMutation = useMutation({
    mutationKey: ["overrides"],
    mutationFn: deleteOverride
  });
  const addOvrMutation = useMutation({
    mutationKey: ["overrides"],
    mutationFn: addOverride
  });

  const makePropChangeHandler = useCallback((index: number, key: keyof Overrides) => {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setOverrides((prev) => {
        const newOverrides = [...prev];
        newOverrides[index][key] = e.target.value;
        return newOverrides;
      });
    };
  }, []);

  const reloadData = useCallback(() => {
    refetch();
    if (data) {
      setOverrides(data.map((ovr) => {
        const unc = new Date(ovr.props.unconverted_mtime);
        const conv = new Date(ovr.props.converted_mtime);
        const proc = new Date(ovr.props.processed_mtime);
        return {
          pattern: ovr.id,
          unconverted_mtime: unc.valueOf() == 0 ? "0" : new Date(unc).toLocaleString(),
          converted_mtime: conv.valueOf() == 0 ? "0" : new Date(conv).toLocaleString(),
          processed_mtime: proc.valueOf() == 0 ? "0" : new Date(proc).toLocaleString()
        };
      }));
    }
  }, [data, refetch]);

  useEffect(() => {
    reloadData();
    setFormErr(null);
  }, [reloadData]);

  const handleOpenModal = () => {
    reloadData();
    onOpen();
  };

  const handleDeleteOverride = (i: number) => {
    setOverrides((prev) => [
      ...prev.slice(0, i),
      ...prev.slice(i + 1)
    ]);
  };

  const handleAddOverride = () => {
    setOverrides((prev) => [
      ...prev,
      {
        pattern: "",
        unconverted_mtime: "",
        converted_mtime: "",
        processed_mtime: ""
      }
    ]);
  };

  const handleSaveOverride = async () => {
    if (data) {
      const ovrToDelete = data.filter((exp) => !overrides.find((ovrExp) => exp.id === ovrExp.pattern));
      for (const ovr of ovrToDelete) {
        await deleteOvrMutation.mutateAsync(ovr.id);
      }
      for (const ovr of overrides) {
        if (ovr.pattern === "") {
          setFormErr("Pattern cannot be blank");
          return;
        }
        const newOvr: Experiment = {
          id: ovr.pattern,
          props: {
            unconverted_mtime: ovr.unconverted_mtime === "0" ? 0 : Date.parse(ovr.unconverted_mtime),
            converted_mtime: ovr.unconverted_mtime === "0" ? 0 : Date.parse(ovr.converted_mtime),
            processed_mtime: ovr.unconverted_mtime === "0" ? 0 : Date.parse(ovr.processed_mtime),
            overridden: true
          }
        };
        await addOvrMutation.mutateAsync(newOvr);
      }
    }
    if (!deleteOvrMutation.isError && !addOvrMutation.isError) {
      onClose();
      refetchInventory();
    }
  };

  return (
    <>
      <Button colorScheme="orange" leftIcon={<SettingsIcon />} onClick={handleOpenModal}>Manage Overrides</Button>

      <Modal isOpen={isOpen} onClose={onClose} closeOnOverlayClick={false}>
        <ModalOverlay />
        <ModalContent maxW="80vw">
          <ModalHeader>Manage Overrides</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {isPending && <p>Loading...</p>}
            {isError && <p>{error.message}</p>}
            {!isPending && !isError && data &&
              <Grid templateColumns='0.1fr repeat(4, 1fr)' gap={2}>
                <GridItem />
                <GridItem>Pattern</GridItem>
                <GridItem>Unconverted Data Modified Time</GridItem>
                <GridItem>Converted Data Modified Time</GridItem>
                <GridItem>Processed Data Modified Time</GridItem>

                {overrides.map((override, i) => (
                  <div style={{ display: "contents" }} key={i}>
                    <GridItem>
                      <Button colorScheme="red" variant="outline" onClick={() => handleDeleteOverride(i)}>
                        –
                      </Button>
                    </GridItem>
                    <GridItem w="100%">
                      <Input
                        placeholder="Pattern"
                        value={override.pattern}
                        onChange={makePropChangeHandler(i, "pattern")}
                      />
                    </GridItem>
                    <GridItem w="100%">
                      <MTimeInput
                        placeholder="Unconverted Data Modified Time"
                        value={override.unconverted_mtime}
                        onChange={makePropChangeHandler(i, "unconverted_mtime")}
                      />
                    </GridItem>
                    <GridItem w="100%">
                      <MTimeInput
                        placeholder="Converted Data Modified Time"
                        value={override.converted_mtime}
                        onChange={makePropChangeHandler(i, "converted_mtime")}
                      />
                    </GridItem>
                    <GridItem w="100%">
                      <MTimeInput
                        placeholder="Processed Data Modified Time"
                        value={override.processed_mtime}
                        onChange={makePropChangeHandler(i, "processed_mtime")}
                      />
                    </GridItem>
                  </div>
                ))}
              </Grid>
            }
            <Button marginTop={4} colorScheme="green" onClick={handleAddOverride}>+ Add Override</Button>
          </ModalBody>

          <ModalFooter>
            {formErr && <Text mr={3}>{formErr}</Text>}
            {deleteOvrMutation.isError && <Text mr={3}>{deleteOvrMutation.error.message}</Text>}
            {addOvrMutation.isError && <Text mr={3}>{addOvrMutation.error.message}</Text>}
            <Button onClick={onClose} mr={3}>Cancel</Button>
            <Button
              onClick={handleSaveOverride}
              colorScheme="blue"
              isLoading={deleteOvrMutation.isPending || addOvrMutation.isPending}
            >
              Save
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

type MTimeInputProps = {
  placeholder: string,
  value: string,
  onChange: React.ChangeEventHandler<HTMLInputElement>
};

const MTimeInput = ({ placeholder, value, onChange }: MTimeInputProps) => {
  return (
    <InputGroup>
      <Popover>
        <PopoverTrigger>
          <InputLeftAddon
            _hover={{ filter: "brightness(90%)" }}
            _active={{ filter: "brightness(80%)" }}
            transition="all 100ms ease"
          >
            <QuestionIcon />
          </InputLeftAddon>
        </PopoverTrigger>
        <PopoverContent>
          <PopoverBody>
            Enter an override last-modified time for the given experiment pattern.
            Any experiments matching the pattern will have their last-modified time overwritten by this value.
            Enter values in the format <b>"YYYY-mm-dd HH:mm:ss AM/PM"</b>, or if the value does not matter, enter <b>0</b>.
          </PopoverBody>
        </PopoverContent>
      </Popover>
      <Input
        placeholder={placeholder}
        borderLeftRadius={0}
        value={value}
        onChange={onChange}
      />
    </InputGroup>
  );
};

export default OverridesPanel;