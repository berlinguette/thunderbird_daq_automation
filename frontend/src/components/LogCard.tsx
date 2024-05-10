import { Badge, Box, Flex } from "@chakra-ui/react";
import { Log } from "../types/Log";

const LogCard = ({ msg }: { msg: Log }) => {
  let colorScheme = "gray";
  let background = "white";
  switch (msg.level) {
    case "CRITICAL":
      colorScheme = "red";
      background = "red.50"
      break;
    case "ERROR":
      colorScheme = "orange";
      background = "orange.50";
      break;
    case "WARNING":
      colorScheme = "yellow";
      background = "yellow.50";
      break;
    case "INFO":
      colorScheme = "white";
      background = "white";
      break;
    case "DEBUG":
      colorScheme = "gray";
      background = "gray.200";
      break;
  }

  return (
    <Flex flexDirection="column" p={2} bg={background} borderRadius="var(--card-radius)" key={msg.timestamp}>
      <Flex gap={2} fontSize="small" color="gray" alignItems="center">
        {new Date(msg.timestamp).toLocaleString()}
        <Badge colorScheme={colorScheme}>{msg.level} {msg.icon}</Badge>
      </Flex>
      <Box>
        {msg.message}
      </Box>
    </Flex>
  )
};

export default LogCard;