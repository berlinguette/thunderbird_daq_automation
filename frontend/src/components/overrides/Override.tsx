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
import { UnstrictOverride } from "./unstrictOverride";
import { produce } from "immer";

type OverrideProps = {
  unstrictOverride: UnstrictOverride;
  steps: string[];
  index: number;
  setUnstrictOverrides: React.Dispatch<
    React.SetStateAction<UnstrictOverride[]>
  >;
};

const Override = ({
  unstrictOverride,
  steps,
  index: i,
  setUnstrictOverrides,
}: OverrideProps) => {
  const makeOnModifyMTime = (stepIndex: number) => {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setUnstrictOverrides(
        produce((draft) => {
          draft[i].analysis_step_overrides[stepIndex].mtime = e.target.value;
        })
      );
    };
  };

  const onModifyPattern: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    setUnstrictOverrides(
      produce((draft) => {
        draft[i].pattern = e.target.value;
      })
    );
  };

  const onDeleteOverride = () => {
    setUnstrictOverrides((prev) => [...prev.slice(0, i), ...prev.slice(i + 1)]);
  };

  return (
    <div style={{ display: "contents" }} key={i}>
      <GridItem>
        <Button colorScheme="red" variant="outline" onClick={onDeleteOverride}>
          –
        </Button>
      </GridItem>
      <GridItem w="100%">
        <Input
          placeholder="Pattern"
          aria-label={`Pattern ${i}`}
          value={unstrictOverride.pattern}
          onChange={onModifyPattern}
        />
      </GridItem>
      {steps.map((step, stepIndex) => (
        <GridItem w="100%">
          <MTimeInput
            placeholder={`${step} Modified Time`}
            aria-label={`${step} Modified Time ${i}`}
            value={
              unstrictOverride.analysis_step_overrides[stepIndex]?.mtime ?? ""
            }
            onChange={makeOnModifyMTime(stepIndex)}
          />
        </GridItem>
      ))}
    </div>
  );
};

type MTimeInputProps = {
  placeholder: string;
  "aria-label": string;
  value: string;
  onChange: React.ChangeEventHandler<HTMLInputElement>;
};

const MTimeInput = ({
  placeholder,
  "aria-label": ariaLabel,
  value,
  onChange,
}: MTimeInputProps) => {
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
