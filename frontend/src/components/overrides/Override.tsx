import { QuestionIcon } from "@chakra-ui/icons";
import {
  Button,
  GridItem,
  Input,
  InputGroup,
  InputLeftAddon,
  Popover,
  PopoverBody,
  PopoverContent,
  PopoverTrigger,
} from "@chakra-ui/react";
import { FlattenedOverride } from "./flattenedOverride";

type OverrideProps = {
  override: FlattenedOverride;
  index: number;
  setOverrides: React.Dispatch<React.SetStateAction<FlattenedOverride[]>>;
};

const Override = ({ override, index: i, setOverrides }: OverrideProps) => {
  const makeOnModifyProp = (
    index: number,
    key: keyof FlattenedOverride
  ) => {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setOverrides((prev) => {
        const newOverrides = [...prev];
        newOverrides[index][key] = e.target.value;
        return newOverrides;
      });
    };
  };

  const onDeleteOverride = (i: number) => {
    setOverrides((prev) => [...prev.slice(0, i), ...prev.slice(i + 1)]);
  };

  return (
    <div style={{ display: "contents" }} key={i}>
      <GridItem>
        <Button
          colorScheme="red"
          variant="outline"
          onClick={() => onDeleteOverride(i)}
        >
          –
        </Button>
      </GridItem>
      <GridItem w="100%">
        <Input
          placeholder="Pattern"
          aria-label={`Pattern ${i}`}
          value={override.pattern}
          onChange={makeOnModifyProp(i, "pattern")}
        />
      </GridItem>
      <GridItem w="100%">
        <MTimeInput
          placeholder="Unconverted Data Modified Time"
          aria-label={`Unconverted Data Modified Time ${i}`}
          value={override.unconverted_mtime}
          onChange={makeOnModifyProp(i, "unconverted_mtime")}
        />
      </GridItem>
      <GridItem w="100%">
        <MTimeInput
          placeholder="Converted Data Modified Time"
          aria-label={`Converted Data Modified Time ${i}`}
          value={override.converted_mtime}
          onChange={makeOnModifyProp(i, "converted_mtime")}
        />
      </GridItem>
      <GridItem w="100%">
        <MTimeInput
          placeholder="Processed Data Modified Time"
          aria-label={`Processed Data Modified Time ${i}`}
          value={override.processed_mtime}
          onChange={makeOnModifyProp(i, "processed_mtime")}
        />
      </GridItem>
    </div>
  );
};

type MTimeInputProps = {
  placeholder: string;
  "aria-label": string
  value: string;
  onChange: React.ChangeEventHandler<HTMLInputElement>;
};

const MTimeInput = ({ placeholder, "aria-label": ariaLabel, value, onChange }: MTimeInputProps) => {
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
            Enter an override last-modified time for the given experiment
            pattern. Any experiments matching the pattern will have their
            last-modified time overwritten by this value. Enter values in the
            format <b>"YYYY-mm-dd HH:mm:ss AM/PM"</b>, or if the value does not
            matter, enter <b>0</b>.
          </PopoverBody>
        </PopoverContent>
      </Popover>
      <Input
        placeholder={placeholder}
        aria-label={ariaLabel}
        borderLeftRadius={0}
        value={value}
        onChange={onChange}
      />
    </InputGroup>
  );
};

export default Override;
