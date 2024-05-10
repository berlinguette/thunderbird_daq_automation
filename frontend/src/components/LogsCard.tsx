import { Box, Card, CardBody, VStack } from "@chakra-ui/react";
import { useContext, useEffect, useRef, useState } from "react";
import { LogsContext } from "../layout/LogListener";

const LogsCard = () => {
  const logs = useContext(LogsContext);
  const logWindowRef = useRef<HTMLDivElement>(null);
  const [scrolledToBottom, setScrolledToBottom] = useState(true);

  const handleScroll = () => {
    if (logWindowRef.current) {
      // https://stackoverflow.com/questions/876115/how-can-i-determine-if-a-div-is-scrolled-to-the-bottom
      const scrolledToBottom = logWindowRef.current.scrollHeight -
        logWindowRef.current.scrollTop - logWindowRef.current.clientHeight < 1;
      setScrolledToBottom(scrolledToBottom);
    }
  };

  useEffect(() => {
    if (logWindowRef.current && scrolledToBottom) {
      logWindowRef.current.scroll({
        behavior: "smooth",
        top: logWindowRef.current.scrollHeight
      });
    }
  }, [logs, scrolledToBottom]);

  return (
    <Card variant="filled" overflowY="scroll" flexGrow={1} ref={logWindowRef} onScroll={handleScroll}>
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