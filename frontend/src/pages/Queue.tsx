import { Button, Flex, Heading, Spinner, Text } from "@chakra-ui/react";
import NavBar from "../layout/NavBar";
import QueueCard from "../components/QueueCard";
import { Analysis } from "../types/Analysis";
import { getAnalyses } from "../api/analyses";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import LogsCard from "../components/LogsCard";

type Analyses = {
  current: Analysis,
  queued: Analysis[]
};

const Queue = () => {
  const queryClient = useQueryClient();
  const { isPending, isFetching, isError, data, error } = useQuery<Analyses>({
    queryKey: ["queue"],
    queryFn: getAnalyses
  });

  return (
    <Flex flexDirection="column" gap={12} padding={6} h="100%">
      <NavBar />
      <Flex gap={8} minHeight={0} flexGrow={1}>
        <Flex flexDir="column" basis="40%" gap={14} flexShrink={0}>
          {isPending && <Text>Loading...</Text>}
          {isError && <Text>{error.message}</Text>}
          {!isPending && !isError && data &&
            <>
              <Flex flexDir="column" gap={4}>
                <Flex alignItems="center" gap={6}>
                  <Heading>In Progress</Heading>
                  <Flex gap={2} fontSize="large">
                    <Button
                      color="gray"
                      variant="ghost"
                      gap={2}
                      onClick={() => queryClient.invalidateQueries({ queryKey: ["queue"] })}
                    >
                      Refresh
                      {isFetching && <Spinner size="sm" speed="0.6s" />}
                    </Button>
                  </Flex>
                </Flex>
                {!data.current && <Text>No analyses in progress.</Text>}
                {data.current &&
                  <QueueCard analysis={data.current} inProgress />
                }
              </Flex>
              <Flex flexDir="column" gap={4}>
                <Heading>Queue</Heading>
                {!data.current && <Text>No analyses queued.</Text>}
                {data.queued && data.queued.map((analysis) => <QueueCard analysis={analysis} />)}
              </Flex>
            </>
          }
        </Flex>
        <Flex flexDirection="column" gap={4} flexGrow={1}>
          <Heading>Logs</Heading>
          <LogsCard />
        </Flex>
      </Flex>
    </Flex>
  )
}

export default Queue;