import processor, session

# r = processor.process("", direct="route set downtown drive = 2001 Tradewinds Dr 77498 > "
#                   "300 Promenade Wy Suite 150, Sugar Land, TX 77478 | September 3rd, 3:00pm-7:00pm")
# r = processor.process("", "route add micro = 2001 Tradewinds Dr 77498 > "
#                           "300 Promenade Wy Suite 150, Sugar Land, TX 77478")
# r = processor.process("", "route set micro = 2001 Tradewinds Dr 77498 > "
#                           "300 Promenade Wy Suite 150, Sugar Land, TX 77478 | September 3rd, 3:00pm-7:00pm")
r = processor.process("", "yes")
# print(session.get_requirement("+13829249240"))
print(r)
