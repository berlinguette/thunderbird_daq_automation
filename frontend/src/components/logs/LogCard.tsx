import { Badge, Box, Flex } from "@chakra-ui/react";
import { Log } from "../../types/Log";
import { logColors } from "../../helpers/logging";

const LogCard = ({ msg }: { msg: Log }) => {
  return (
    <Flex flexDirection="column" p={2} bg={logColors[msg.level].background} borderRadius="var(--card-radius)" key={msg.timestamp}>
      <Flex gap={2} fontSize="small" color="gray" alignItems="center">
        {new Date(msg.timestamp).toLocaleString()}
        <Badge colorScheme={logColors[msg.level].colorScheme}>{msg.level} {msg.icon}</Badge>
      </Flex>
      <Box>
        {msg.message}
      </Box>
    </Flex>
  );
};

export default LogCard;