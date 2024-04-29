import { ChevronDownIcon } from "@chakra-ui/icons";
import { Button, Menu, MenuButton, MenuItem, MenuList } from "@chakra-ui/react";
import { CheckedExperiments } from "./Inventory";
import { AnalysisFilter, startAnalysis } from "../api/analyses";
import { useMutation } from "@tanstack/react-query";

type AnalyzeMenuProps = {
  analyzeFilter: "all" | "selected",
  checkedExperiments: CheckedExperiments,
  disabled?: boolean
  outline?: boolean
};

const AnalyzeMenu = ({ analyzeFilter, checkedExperiments, disabled = false, outline = false }: AnalyzeMenuProps) => {
  const mutation = useMutation({
    mutationFn: startAnalysis
  });

  const makeAnalyzeHandler = (type: "all" | "convert" | "process") => async () => {
    const body: AnalysisFilter = {
      convert_unconverted: type === "convert" || type === "all",
      process_converted: type === "process" || type === "all"
    };

    if (analyzeFilter !== "all") {
      const checkedIds = Object.entries(checkedExperiments).map(([id, checked]) => checked ? id : "");
      body.pattern = `(${checkedIds.filter((v) => v !== "").join("|")})`;
    }
    mutation.mutate(body);
  }

  return (
    <>
      <Menu>
        <MenuButton
          as={Button}
          colorScheme="blue"
          isDisabled={disabled}
          rightIcon={<ChevronDownIcon />}
          isLoading={mutation.isPending}
          variant={outline ? "outline" : "solid"}
        >
          Analyze {analyzeFilter == "all" ? "All" : "Selected"}
        </MenuButton>
        <MenuList>
          <MenuItem onClick={makeAnalyzeHandler("all")}>All</MenuItem>
          <MenuItem onClick={makeAnalyzeHandler("convert")}>Convert Only</MenuItem>
          <MenuItem onClick={makeAnalyzeHandler("process")}>Process Only</MenuItem>
        </MenuList>
      </Menu>
      {mutation.isError && <p>{mutation.error.message}</p>}
    </>
  );
};

export default AnalyzeMenu;