"""Cosmetic costume only; does not modify solved motion or fabrication geometry."""

def appearance():
    # y,z outline in mm: tall ears, cheeks, tapered torso, feet and tail.
    outline = [(-30,22),(-32,65),(-13,45),(0,48),(13,45),(32,65),
               (30,22),(37,8),(32,-25),(23,-43),(26,-54),(12,-49),
               (0,-65),(-12,-49),(-26,-54),(-23,-43),(-32,-25),(-37,8)]
    front, back = -42, -39
    faces = [{'points':[[front,y,z] for y,z in outline], 'color':'#28212b'},
             {'points':[[back,y,z] for y,z in outline], 'color':'#211b26'}]
    for a,b in zip(outline,outline[1:]+outline[:1]):
        faces.append({'points':[[front,*a],[back,*a],[back,*b],[front,*b]],'color':'#352b38'})
    def detail(points,color):
        faces.append({'points':[[front-0.8,y,z] for y,z in points],'color':color})
    detail([(-28,55),(-25,28),(-16,40)],'#795263')
    detail([(28,55),(25,28),(16,40)],'#795263')
    detail([(-20,25),(-8,23),(-12,18),(-19,19)],'#e9b95e')
    detail([(20,25),(8,23),(12,18),(19,19)],'#e9b95e')
    detail([(-5,13),(5,13),(0,8)],'#ae7884')
    detail([(-9,4),(-5,-3),(-3,4)],'#eee4d1')
    detail([(9,4),(5,-3),(3,4)],'#eee4d1')
    detail([(-17,-8),(0,-2),(17,-8),(14,-29),(0,-43),(-14,-29)],'#453543')
    return faces
