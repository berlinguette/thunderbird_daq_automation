import { Badge, Box, Flex } from "@chakra-ui/react";
import { Log } from "../types/Log";

const LogCard = ({ msg }: { msg: Log }) => {
  let colorScheme = "gray";
  switch (msg.level) {
    case "CRITICAL":
      colorScheme = "red";
      break;
    case "ERROR":
      colorScheme = "orange";
      break;
    case "WARNING":
      colorScheme = "yellow";
      break;
    case "INFO":
      colorScheme = "gray";
      break;
    case "DEBUG":
      colorScheme = "white";
      break;
  }

  return (
    <Flex flexDirection="column" p={2} bg="white" borderRadius="var(--card-radius)" key={msg.timestamp}>
      <Flex gap={2} fontSize="small" color="gray" alignItems="center">
        {msg.timestamp}
        <Badge colorScheme={colorScheme}>{msg.level}</Badge>
      </Flex>
      <Box>
        {msg.message}
      </Box>
    </Flex>
  )
};

export default LogCard;