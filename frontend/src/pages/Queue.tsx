import {
  Box,
  Button,
  Flex,
  Heading,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Spinner,
  Text,
} from "@chakra-ui/react";
import NavBar from "../layout/NavBar";
import QueueCard from "../components/QueueCard";
import LogsDisplay from "../components/logs/LogsDisplay";
import { ChevronDownIcon } from "@chakra-ui/icons";
import { useState } from "react";
import { logColors, orderedLogLevels } from "../helpers/logging";
import { LogLevels } from "../types/Log";
import { useGetAnalyses } from "../hooks/useAnalyses";

const Queue = () => {
  const { isPending, isFetching, isError, analyses, error, refetch } =
    useGetAnalyses();
  const [lowestLogLevel, setLowestLogLevel] = useState<LogLevels>("INFO");

  return (
    <Flex flexDirection="column" gap={12} padding={6} h="100%">
      <NavBar />
      <Flex gap={8} minHeight={0} flexGrow={1}>
        <Flex flexDir="column" basis="40%" gap={14} flexShrink={0}>
          {isPending && <Text>Loading...</Text>}
          {isError && <Text>{error?.message}</Text>}
          {!isPending && !isError && analyses && (
            <>
              <Flex flexDir="column" gap={4}>
                <Flex alignItems="center" gap={6}>
                  <Heading>In Progress</Heading>
                  <Flex gap={2} fontSize="large">
                    <Button
                      color="gray"
                      variant="ghost"
                      gap={2}
                      onClick={() => refetch()}
                    >
                      Refresh
                      {isFetching && <Spinner size="sm" speed="0.6s" />}
                    </Button>
                  </Flex>
                </Flex>
                {!analyses.current && <Text>No analyses in progress.</Text>}
                {analyses.current && (
                  <QueueCard analysis={analyses.current} inProgress />
                )}
              </Flex>
              <Flex flexDir="column" gap={4}>
                <Heading>Queue</Heading>
                {!analyses.current && <Text>No analyses queued.</Text>}
                {analyses.queued &&
                  analyses.queued.map((analysis) => (
                    <QueueCard analysis={analysis} />
                  ))}
              </Flex>
            </>
          )}
        </Flex>
        <Flex flexDirection="column" gap={4} flexGrow={1}>
          <Flex gap={4}>
            <Heading>Logs</Heading>
            <Menu>
              <MenuButton
                as={Button}
                rightIcon={<ChevronDownIcon />}
                variant="ghost"
              >
                Log level:{" "}
                <Box color={logColors[lowestLogLevel].textColor}>
                  {lowestLogLevel}
                </Box>
              </MenuButton>
              <MenuList>
                {orderedLogLevels.map((logLevel) => (
                  <MenuItem
                    color={logColors[logLevel].textColor}
                    onClick={() => setLowestLogLevel(logLevel)}
                    key={logLevel}
                  >
                    {logLevel}
                  </MenuItem>
                ))}
              </MenuList>
            </Menu>
          </Flex>
          <LogsDisplay lowestLogLevel={lowestLogLevel} />
        </Flex>
      </Flex>
    </Flex>
  );
};

export default Queue;
