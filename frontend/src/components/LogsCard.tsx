import { Box, Card, CardBody, VStack } from "@chakra-ui/react";
import { useContext, useEffect, useRef } from "react";
import { LogsContext } from "../layout/LogListener";

const LogsCard = () => {
  const logs = useContext(LogsContext);
  const logWindowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logWindowRef.current) {
      logWindowRef.current.scroll({
        behavior: "smooth",
        top: logWindowRef.current.scrollHeight
      });
    }
  }, [logs]);

  return (
    <Card variant="filled" overflowY="scroll" flexGrow={1} ref={logWindowRef}>
      <CardBody p={4}>
        <VStack spacing={3} align="stretch">
          {logs.map((msg) => (
            <Box p={2} bg="white" borderRadius="var(--card-radius)" key={msg}>
              {msg}
            </Box>
          ))}
        </VStack>
      </CardBody>
    </Card>
  )
};

export default LogsCard;