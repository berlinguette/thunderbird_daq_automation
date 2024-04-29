import { QuestionIcon, SettingsIcon } from "@chakra-ui/icons";
import { Button, Grid, GridItem, Input, InputGroup, InputLeftAddon, Modal, ModalBody, ModalCloseButton, ModalContent, ModalFooter, ModalHeader, ModalOverlay, Popover, PopoverBody, PopoverContent, PopoverTrigger, useDisclosure } from "@chakra-ui/react";
import { Experiment } from "../types/Experiment";
import { useCallback, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getOverrides } from "../api/overrides";

type Overrides = {
  pattern: string,
  unconverted_mtime: string,
  converted_mtime: string,
  processed_mtime: string
}

const OverridesPanel = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [overrides, setOverrides] = useState<Overrides[]>([]);

  const queryClient = useQueryClient();
  const { isPending, isError, data, error } = useQuery<Experiment[]>({
    queryKey: ["overrides"],
    queryFn: getOverrides,
    staleTime: Infinity
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

  useEffect(() => {
    if (data) {
      setOverrides(data.map((ovr) => {
        return {
          pattern: ovr.id,
          unconverted_mtime: new Date(ovr.props.unconverted_mtime).toLocaleString(),
          converted_mtime: new Date(ovr.props.converted_mtime).toLocaleString(),
          processed_mtime: new Date(ovr.props.processed_mtime).toLocaleString()
        };
      }));
    }
  }, [data]);

  const handleOpenModal = () => {
    queryClient.invalidateQueries({ queryKey: ["overrides"] });
    onOpen();
  }

  const handleSaveOverride = () => {

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
                      <Button colorScheme="red" variant="outline">–</Button>
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
          </ModalBody>

          <ModalFooter>
            <Button onClick={onClose} mr={3}>Close</Button>
            <Button onClick={handleSaveOverride} colorScheme="blue">Save</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  )
}

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
  )
}

export default OverridesPanel;